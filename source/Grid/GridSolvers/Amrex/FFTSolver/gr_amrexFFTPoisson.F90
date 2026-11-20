!!****if* source/Grid/GridSolvers/Amrex/FFTSolver/gr_amrexFFTPoisson
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
!!  gr_amrexFFTPoisson
!!
!!  DESCRIPTION
!!
!!  Fortran bindings to AMReX's FFT Poisson solver (gr_amrexFFTPoissonFi.cxx), for
!!  gr_amrexFFTSolvePoisson. AMReX has no Fortran interface to its FFT solvers, so the C++
!!  file wraps FFT::Poisson in C functions.
!!
!!***

#include "constants.h"
#include "Simulation.h"

module gr_amrexFFTPoisson

   use iso_c_binding, ONLY: c_int, c_ptr

   implicit none

   ! the boundary codes of gr_amrexFFTPoissonFi.cxx
   integer(c_int), parameter :: FFT_PERIODIC = 0, FFT_NEUMANN = 1, FFT_DIRICHLET = 2

   interface
      subroutine gr_amrex_fft_poisson_solve(soln, rhs, geom, bcLow, bcHigh) bind(c)
         import :: c_int, c_ptr
         type(c_ptr), value :: soln, rhs, geom
         integer(c_int), intent(in) :: bcLow(*), bcHigh(*)
      end subroutine gr_amrex_fft_poisson_solve

      subroutine gr_amrex_fft_poisson_gradient(soln, gradients, geom) bind(c)
         import :: c_ptr
         type(c_ptr), value :: soln, geom
         type(c_ptr), intent(in) :: gradients(*)
      end subroutine gr_amrex_fft_poisson_gradient
   end interface

contains

   integer(c_int) function fftBoundary(bcType)
      use Driver_interface, ONLY: Driver_abort
      use Grid_interface, ONLY: GRID_PDE_BND_PERIODIC, GRID_PDE_BND_NEUMANN, GRID_PDE_BND_DIRICHLET

      integer, intent(in) :: bcType

      select case (bcType)
      case (GRID_PDE_BND_PERIODIC)
         fftBoundary = FFT_PERIODIC
      case (GRID_PDE_BND_NEUMANN)
         fftBoundary = FFT_NEUMANN
      case (GRID_PDE_BND_DIRICHLET)
         fftBoundary = FFT_DIRICHLET
      case default
         fftBoundary = FFT_PERIODIC
         call Driver_abort("[gr_amrexFFTSolvePoisson] BC not implemented for the FFT solver")
      end select
   end function fftBoundary

end module gr_amrexFFTPoisson
