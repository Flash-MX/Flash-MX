// Solves Grid_solvePoisson's equation, the Laplacian of the solution equal to the RHS, with
// AMReX's FFT Poisson solver on a single level. The solver holds FFT plans and data layouts
// that are costly to build, so it is kept between solves and rebuilt only when the domain or
// the boundary conditions change.
#include <AMReX_Config.H>
#include <AMReX_Version.H>

// AMReX writes AMREX_USE_FFT into AMReX_Config.H only when configured with --enable-fft=yes.
// The FFT Poisson solver's Neumann and Dirichlet boundaries and the guard-cell fill in solve(),
// which gr_amrex_fft_poisson_gradient relies on, arrived in late 2024 releases, so 25.00 is
// required. A build from an untagged checkout has release number 0, so its version is not checked.
#if !defined(AMREX_USE_FFT)
#error "AmrexFFT=True needs AMReX 25.00 or later, configured with --enable-fft=yes"
#elif AMREX_RELEASE_NUMBER > 0 && AMREX_RELEASE_NUMBER < 250000
#error "AmrexFFT=True needs AMReX 25.00 or later"
#else
#include <AMReX_FFT_Poisson.H>
#endif
#include <AMReX.H>
#include <AMReX_Geometry.H>
#include <AMReX_MultiFab.H>

#include <memory>

using namespace amrex;

namespace {
    using BoundaryPairs = Array<std::pair<FFT::Boundary, FFT::Boundary>, AMREX_SPACEDIM>;

    std::unique_ptr<FFT::Poisson<MultiFab>> poissonSolver;
    Box solverDomain;
    BoundaryPairs solverBoundaries;

    // The codes of gr_amrexFFTPoisson.F90. The solution is reflected evenly across a
    // Neumann boundary and oddly across a Dirichlet one.
    FFT::Boundary fftBoundary (int code)
    {
        switch (code) {
        case 0: return FFT::Boundary::periodic;
        case 1: return FFT::Boundary::even;
        case 2: return FFT::Boundary::odd;
        default: amrex::Abort("gr_amrexFFTPoisson: unknown boundary code");
        }
        return FFT::Boundary::periodic;
    }

    FFT::Poisson<MultiFab>& solverFor (Geometry const& geom, BoundaryPairs const& boundaries)
    {
        if (!poissonSolver || geom.Domain() != solverDomain || boundaries != solverBoundaries) {
            bool const firstSolver = !poissonSolver;
            poissonSolver = std::make_unique<FFT::Poisson<MultiFab>>(geom, boundaries);
            solverDomain = geom.Domain();
            solverBoundaries = boundaries;
            // The solver's FFT plans and communicators must be freed before AMReX finalizes FFT.
            // AMReX runs these callbacks last registered first, and registers FFT's own in
            // amrex::Initialize, so this one, registered later, frees the solver before it.
            if (firstSolver) {
                amrex::ExecOnFinalize([] () { poissonSolver.reset(); });
            }
        }
        return *poissonSolver;
    }
}

extern "C" {

    // Also fills one layer of the solution's guard cells, from the neighboring boxes and
    // from the boundary conditions.
    void gr_amrex_fft_poisson_solve (MultiFab* soln, MultiFab const* rhs, Geometry const* geom,
                                     int const* bcLow, int const* bcHigh)
    {
        BoundaryPairs boundaries;
        for (int axis = 0; axis < AMREX_SPACEDIM; ++axis) {
            boundaries[axis] = {fftBoundary(bcLow[axis]), fftBoundary(bcHigh[axis])};
        }
        solverFor(*geom, boundaries).solve(*soln, *rhs);
    }

    // The gradient on every face of the solution's boxes, as the multigrid solver returns
    // through iGrad: the difference of the cells on either side, so on a domain face the
    // guard cell gr_amrex_fft_poisson_solve filled from the boundary condition.
    void gr_amrex_fft_poisson_gradient (MultiFab const* soln, MultiFab* const* gradients,
                                        Geometry const* geom)
    {
        for (int axis = 0; axis < AMREX_SPACEDIM; ++axis) {
            MultiFab& gradient = *gradients[axis];
            AMREX_ASSERT(gradient.DistributionMap() == soln->DistributionMap());
            Real const dxInverse = geom->InvCellSize(axis);
            int const di = (axis == 0), dj = (axis == 1), dk = (axis == 2);
            for (MFIter mfi(gradient); mfi.isValid(); ++mfi) {
                Array4<Real const> const solution = soln->const_array(mfi);
                Array4<Real> const faceGradient = gradient.array(mfi);
                ParallelFor(mfi.validbox(), [=] AMREX_GPU_DEVICE (int i, int j, int k)
                {
                    faceGradient(i, j, k) = (solution(i, j, k) - solution(i - di, j - dj, k - dk)) * dxInverse;
                });
            }
        }
    }

}
