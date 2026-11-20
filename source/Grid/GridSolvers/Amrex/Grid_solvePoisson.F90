!!****if* source/Grid/GridSolvers/Amrex/Grid_solvePoisson
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
!!  Grid_solvePoisson
!!
!!  SYNOPSIS
!!
!!  call Grid_solvePoisson(integer(IN) :: iSoln,
!!                         integer(IN) :: iSrc,
!!                         integer(IN) :: bcTypes(6),
!!                         real(IN)    :: bcValues(2,6),
!!                         real(INOUT) :: poisfact,
!!                         integer(IN), optional :: iGrad)
!!
!!  DESCRIPTION
!!
!!  Solves the Poisson equation with one of AMReX's solvers: the FFT solver
!!  (gr_amrexFFTSolvePoisson), selected at runtime with gr_amrexPoisson_useFFT when it is
!!  built (AmrexFFT=True). Otherwise multigrid (gr_amrexMultigridSolvePoisson).
!!
!!***

#include "Simulation.h"

subroutine Grid_solvePoisson(iSoln, iSrc, bcTypes, bcValues, poisfact, iGrad)
   use Timers_interface, ONLY: Timers_start, Timers_stop
   use gr_amrexPoissonInterface, ONLY: gr_amrexMultigridSolvePoisson
#ifdef FLASHX_AMREX_FFT
   use RuntimeParameters_interface, ONLY: RuntimeParameters_get
   use gr_amrexPoissonInterface, ONLY: gr_amrexFFTSolvePoisson
#endif

   implicit none

   integer, intent(in) :: iSoln, iSrc
   integer, intent(in) :: bcTypes(6)
   real, intent(in) :: bcValues(2, 6)
   real, intent(inout) :: poisfact
   integer, intent(in), optional :: iGrad

#ifdef FLASHX_AMREX_FFT
   logical :: useFFT
#endif

   call Timers_start("Grid_solvePoisson")

#ifdef FLASHX_AMREX_FFT
   call RuntimeParameters_get("gr_amrexPoisson_useFFT", useFFT)
   if (useFFT) then
      call gr_amrexFFTSolvePoisson(iSoln, iSrc, bcTypes, bcValues, poisfact, iGrad)
      call Timers_stop("Grid_solvePoisson")
      return
   end if
#endif

   call gr_amrexMultigridSolvePoisson(iSoln, iSrc, bcTypes, bcValues, poisfact, iGrad)

   call Timers_stop("Grid_solvePoisson")

end subroutine Grid_solvePoisson
