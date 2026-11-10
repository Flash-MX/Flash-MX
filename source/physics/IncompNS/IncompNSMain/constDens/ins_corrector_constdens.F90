!!
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
!!**
#include "Simulation.h"
#include "constants.h"

subroutine ins_corrector_constdens(uni, vni, wni, pxn1, pyn1, pzn1, pxn0, pyn0, pzn0, &
                                   ix1, ix2, jy1, jy2, kz1, kz2, &
                                   dt, dx, dy, dz)

   ! This routine computes the corrected divergence-free velocities.

   implicit none

   INTEGER, INTENT(IN) :: ix1, ix2, jy1, jy2, kz1, kz2
   REAL, INTENT(IN) :: dt, dx, dy, dz
   REAL, DIMENSION(:, :, :), INTENT(IN) :: pxn0, pyn0, pzn0
   REAL, DIMENSION(:, :, :), INTENT(INOUT) :: uni, vni, wni, pxn1, pyn1, pzn1

   uni(ix1:ix2 + 1, jy1:jy2, kz1:kz2) = uni(ix1:ix2 + 1, jy1:jy2, kz1:kz2) &
                                  - dt*pxn0(ix1:ix2 + 1, jy1:jy2, kz1:kz2)

   vni(ix1:ix2, jy1:jy2 + 1, kz1:kz2) = vni(ix1:ix2, jy1:jy2 + 1, kz1:kz2) &
                                  - dt*pyn0(ix1:ix2, jy1:jy2 + 1, kz1:kz2)

   pxn1(ix1:ix2 + 1, jy1:jy2, kz1:kz2) = pxn1(ix1:ix2 + 1, jy1:jy2, kz1:kz2) - pxn0(ix1:ix2 + 1, jy1:jy2, kz1:kz2)
   pyn1(ix1:ix2, jy1:jy2 + 1, kz1:kz2) = pyn1(ix1:ix2, jy1:jy2 + 1, kz1:kz2) - pyn0(ix1:ix2, jy1:jy2 + 1, kz1:kz2) 

#if NDIM == MDIM
   wni(ix1:ix2, jy1:jy2, kz1:kz2 + 1) = wni(ix1:ix2, jy1:jy2, kz1:kz2 + 1) &
                                  - dt*pzn0(ix1:ix2, jy1:jy2, kz1:kz2 + 1)

   pzn1(ix1:ix2, jy1:jy2, kz1:kz2 + 1) = pzn1(ix1:ix2, jy1:jy2, kz1:kz2 + 1) - pzn0(ix1:ix2, jy1:jy2, kz1:kz2 + 1)
#endif

end subroutine ins_corrector_constdens
