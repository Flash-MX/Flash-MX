!!****f* source/Driver/Driver_evolvePhysics
!! NOTICE
!!  Copyright 2024 UChicago Argonne, LLC and contributors
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
!!  Driver_evolvePhysics
!!
!! SYNOPSIS
!!
!!  call Driver_evolvePhysics()
!!
!! DESCRIPTION
!!
!!  Stub implementation of Driver_evolvePhysics.
!!  This routine contains the per-timestep physics calls extracted from
!!  Driver_evolveAll. Real implementations override this in driver-specific
!!  subdirectories (e.g., DriverMain/Incomp/).
!!
!!  The routine has the same signature as Driver_evolveAll (no arguments).
!!  It is called once per timestep from within the evolution loop in
!!  Driver_evolveAll.
!!
!!***

#ifdef DEBUG_ALL
#define DEBUG_DRIVER
#endif

subroutine Driver_evolvePhysics()

   implicit none

   ! Stub: does nothing. Override in DriverMain subdirectories.
   return

end subroutine Driver_evolvePhysics
