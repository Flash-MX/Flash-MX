!!****if* source/numericalTools/MoL/MoLMain/ERK/ml_finalize
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
!!      ml_finalize
!!
!!  SYNOPSIS
!!
!!      call ml_finalize()
!!
!!  DESCRIPTION
!!
!!      Finalize a method of lines unit implementation
!!
!!  ARGUMENTS
!!
!!
!!***
subroutine ml_finalize()
   use ml_data, only: ml_A, ml_b, ml_c, ml_K

   implicit none

   if (allocated(ml_A)) deallocate (ml_A)
   if (allocated(ml_b)) deallocate (ml_b)
   if (allocated(ml_c)) deallocate (ml_c)
   if (allocated(ml_K)) deallocate (ml_K)
end subroutine ml_finalize
