!!***if* source/physics/sourceTerms/Heater/HeaterMain/Heater_lsReInit
!!
!! NOTICE
!!  Copyright 2023 UChicago Argonne, LLC and contributors
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
!!***
!!REORDER(4): solnData, face[xyz]Data

#include "Simulation.h"
#include "constants.h"

subroutine Heater_lsReInit(solnData,xcell,ycell,zcell,boundBox,logc, higc, stime,lblock)

  use Timers_interface, ONLY: Timers_start, Timers_stop
  use Heater_data
  use Heater_type, ONLY: Heater_type_t
  use Driver_interface, ONLY: Driver_abort
  
  implicit none
  real, dimension(:, :, :, :)  :: solnData
  real, dimension(:), intent(in)        :: xcell, ycell, zcell
  real, dimension(LOW:HIGH, MDIM), intent(in)     :: boundBox
  integer, dimension(MDIM),intent(in)   :: logc, higc
  real, intent(in)                      :: stime
  integer, intent(in)                   :: lblock
  
!----------------------------------------------------------------------------------------
  type(Heater_type_t), pointer  :: heater
  integer :: ix1, ix2, jy1, jy2, kz1, kz2
  integer :: i, j, k, htr, isite
  real    :: idfun, iseedY, iseedX, iseedZ, iradius
  
  !----------------------------------------------------------------------------------------
  
  call Timers_start("Heater_lsReInit")

#ifdef MULTIPHASE_EVAPORATION
  ix1=logc(IAXIS); ix2=higc(IAXIS)
  jy1=logc(JAXIS); jy2=higc(JAXIS)
  kz1=logc(KAXIS); kz2=higc(KAXIS)    
  
  
  do htr = 1, htr_numHeaters
     
     heater => htr_heaterInfo(htr)

     ! Every block stamps the seeds listed by Heater_tagSites, so seeds
     ! near a block boundary are not cut off
     if (.not. any(heater%siteReseed)) cycle

     do isite = 1, heater%numSitesAll

        if (.not. heater%siteReseed(isite)) cycle

        iradius = heater%seedRadius
        iseedX = heater%xSiteInit(isite)
        iseedZ = heater%zSiteInit(isite)
        if (abs(heater%ySiteInit(isite)-htr_yMin) .lt. abs(heater%ySiteInit(isite)-htr_yMax)) then
           iseedY = heater%ySiteInit(isite)+heater%seedHeight
        else
           iseedY = heater%ySiteInit(isite)-heater%seedHeight
        end if

        do k = kz1, kz2
           do j = jy1, jy2
              do i = ix1, ix2
                 idfun = iradius-sqrt((xcell(i)-iseedX)**2+(ycell(j)-iseedY)**2+(zcell(k)-iseedZ)**2)
                 solnData(DFUN_VAR,i, j, k) = max(solnData(DFUN_VAR,i, j, k), idfun)
              end do
           end do
        end do

     end do
  end do

#endif
  
  call Timers_stop("Heater_lsReInit")
  
end subroutine Heater_lsReInit
