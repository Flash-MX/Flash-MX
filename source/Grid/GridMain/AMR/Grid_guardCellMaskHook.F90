!!****if* source/Grid/GridMain/AMR/Grid_guardCellMaskHook
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
!! NAME
!!
!!  Grid_guardCellMaskHook
!!
!! SYNOPSIS
!!
!!  call Grid_guardCellMaskHook(logical(INOUT)  :: ccmask)
!!
!! DESCRIPTION
!! Hook for masked filling of guardcells 
!!
!! ARGUMENTS
!!
!!   ccmask : the mask
!!
!!
!!
!!***

subroutine Grid_guardCellMaskHook(ccMask)
  use gr_specificData, ONLY: gr_enableMaskedGCFill
  implicit none
  logical,intent(INOUT) :: ccMask(*)

  if (gr_enableMaskedGCFill) then

     call Simulation_guardCellMaskHook(ccMask)

     ! ... add calls to other units if necessary ...

  end if

end subroutine Grid_guardCellMaskHook
