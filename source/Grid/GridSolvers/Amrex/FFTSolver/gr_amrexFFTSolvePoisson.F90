!!****if* source/Grid/GridSolvers/Amrex/FFTSolver/gr_amrexFFTSolvePoisson
!! NOTICE
!!  Copyright 2022 UChicago Argonne, LLC and contributors
!!
!!  Licensed under the Apache License, Version 2.0 (the "License");
!!  you may not use this file except in compliance with the License.
!!
!!  Unless required by applicable law or agreed to in writing, software
!!  distributed under the License is distributed on an "AS IS" BASIS,
!!  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
!!  See the License for the specific language governing permissions and
!!  limitations under the License.
!!
!!  NAME
!!
!!  gr_amrexFFTSolvePoisson
!!
!!  SYNOPSIS
!!
!!  call gr_amrexFFTSolvePoisson(integer(IN) :: iSoln,
!!                               integer(IN) :: iSrc,
!!                               integer(IN) :: bcTypes(6),
!!                               real(IN)    :: bcValues(2,6),
!!                               real(INOUT) :: poisfact,
!!                               integer(IN), optional :: iGrad)
!!
!!  DESCRIPTION
!!
!!  Solves the Laplacian of iSoln equal to iSrc directly, with AMReX's FFT Poisson solver, on a
!!  single level of uniform cells. Grid_solvePoisson (Grid/GridSolvers/Amrex) calls it when
!!  gr_amrexPoisson_useFFT is true.
!!
!!  ARGUMENTS
!!
!!  iSoln    - the cell-centered variable for the solution
!!  iSrc     - the cell-centered variable for the right-hand side
!!  bcTypes  - the boundary type of each domain face: GRID_PDE_BND_PERIODIC,
!!             GRID_PDE_BND_NEUMANN or GRID_PDE_BND_DIRICHLET
!!  bcValues - the boundary values, not used (treated as 0)
!!  poisfact - scaling factor, not used (treated as 1)
!!  iGrad    - the face-centered variable for the solution's gradient
!!
!!  NOTES
!!
!!  As with the multigrid solver, the boundary conditions are homogeneous. The solution also
!!  gets one layer of guard cells, from the neighboring boxes and the boundary conditions.
!!
!!***

#include "constants.h"
#include "Simulation.h"

subroutine gr_amrexFFTSolvePoisson(iSoln, iSrc, bcTypes, bcValues, poisfact, iGrad)
   use iso_c_binding, ONLY: c_int, c_ptr
   use Timers_interface, ONLY: Timers_start, Timers_stop
   use Driver_interface, ONLY: Driver_abort
   use amrex_amr_module, ONLY: amrex_geom, amrex_get_finest_level
   use amrex_multifab_module, ONLY: amrex_multifab, amrex_multifab_build_alias, amrex_multifab_destroy
   use gr_physicalMultifabs, ONLY: unk, facevars
   use gr_amrexFFTPoisson, ONLY: gr_amrex_fft_poisson_solve, gr_amrex_fft_poisson_gradient, fftBoundary

   implicit none

   integer, intent(in) :: iSoln, iSrc
   integer, intent(in) :: bcTypes(6)
   real, intent(in) :: bcValues(2, 6)
   real, intent(inout) :: poisfact
   integer, intent(in), optional :: iGrad

   type(amrex_multifab) :: solution, rhs
   type(amrex_multifab) :: gradients(NDIM)
   type(c_ptr) :: gradientPtrs(NDIM)
   integer(c_int) :: bcLow(NDIM), bcHigh(NDIM)
   integer :: axis

   call Timers_start("gr_amrexFFTSolvePoisson")

   ! the finest level is read each solve because refinement can add levels during the run
   if (amrex_get_finest_level() /= 0) then
      call Driver_abort("[gr_amrexFFTSolvePoisson] the FFT solver needs a single level")
   end if

   do axis = 1, NDIM
      bcLow(axis) = fftBoundary(bcTypes(2*axis - 1))
      bcHigh(axis) = fftBoundary(bcTypes(2*axis))
   end do

   call amrex_multifab_build_alias(solution, unk(0), iSoln, 1)
   call amrex_multifab_build_alias(rhs, unk(0), iSrc, 1)
   call gr_amrex_fft_poisson_solve(solution%p, rhs%p, amrex_geom(0)%p, bcLow, bcHigh)

   if (present(iGrad)) then
      do axis = 1, NDIM
         call amrex_multifab_build_alias(gradients(axis), facevars(axis, 0), iGrad, 1)
         gradientPtrs(axis) = gradients(axis)%p
      end do
      call gr_amrex_fft_poisson_gradient(solution%p, gradientPtrs, amrex_geom(0)%p)
      do axis = 1, NDIM
         call amrex_multifab_destroy(gradients(axis))
      end do
   end if

   call amrex_multifab_destroy(solution)
   call amrex_multifab_destroy(rhs)

   call Timers_stop("gr_amrexFFTSolvePoisson")

end subroutine gr_amrexFFTSolvePoisson
