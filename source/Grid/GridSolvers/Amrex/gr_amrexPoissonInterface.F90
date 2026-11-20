!!****ih* source/Grid/GridSolvers/Amrex/gr_amrexPoissonInterface
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
!!  gr_amrexPoissonInterface
!!
!!  DESCRIPTION
!!
!!  Interfaces to the AMReX Poisson solvers that Grid_solvePoisson dispatches to: multigrid
!!  (Amrex/MultigridSolver) and FFT (Amrex/FFTSolver, built with AmrexFFT=True).
!!
!!***

module gr_amrexPoissonInterface

   implicit none

   interface
      subroutine gr_amrexMultigridSolvePoisson(iSoln, iSrc, bcTypes, bcValues, poisfact, iGrad)
         implicit none
         integer, intent(in) :: iSoln, iSrc
         integer, intent(in) :: bcTypes(6)
         real, intent(in) :: bcValues(2, 6)
         real, intent(inout) :: poisfact
         integer, intent(in), optional :: iGrad
      end subroutine gr_amrexMultigridSolvePoisson
   end interface

   interface
      subroutine gr_amrexFFTSolvePoisson(iSoln, iSrc, bcTypes, bcValues, poisfact, iGrad)
         implicit none
         integer, intent(in) :: iSoln, iSrc
         integer, intent(in) :: bcTypes(6)
         real, intent(in) :: bcValues(2, 6)
         real, intent(inout) :: poisfact
         integer, intent(in), optional :: iGrad
      end subroutine gr_amrexFFTSolvePoisson
   end interface

end module gr_amrexPoissonInterface
