!!****if* source/Grid/GridMain/paramesh/gr_makeMaskConsistent
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
!!
!! NAME
!!
!!  gr_makeMaskConsistent
!!
!! SYNOPSIS
!!
!!  call gr_makeMaskConsistent(integer,intent(IN)  :: gridDataStruct)
!!
!! DESCRIPTION
!!
!!  Makes sure that variables needed for guard cell filling are not masked
!!  out in the PARAMESH mask gcell_on_cc: when a mass-specific variable is
!!  requested and conversion to conserved form is used for interpolation,
!!  density is added to the mask; with monotonic interpolation, species are
!!  added as needed. Units may adjust the mask further through
!!  Grid_guardCellMaskHook.
!!
!! ARGUMENTS
!!
!!   gridDataStruct : indicates a variable that the caller needs, as an index into unk
!!
!! NOTES
!!
!!  Currently this routine is applicable to only cell centered data.
!!
!!***


subroutine gr_makeMaskConsistent(gridDataStruct)

  use Grid_interface,   ONLY : Grid_guardCellMaskHook
  use Grid_data, ONLY : gr_vartypes, gr_convertToConsvdForMeshCalls,gr_convertToConsvdInMeshInterp

  use physicaldata, ONLY : gcell_on_cc
  implicit none

#include "constants.h"
#include "Simulation.h"

  integer,intent(IN) :: gridDataStruct

  integer :: iref

  !! If density is not a variable in the current simulation, the density rules
  !! below are skipped.
  logical :: dens=.true.
#ifndef DENS_VAR
#define DENS_VAR 1
  dens=.false.
#endif

  if((gridDataStruct/=CENTER).and.(gridDataStruct/=CENTER_FACES)) return

  !! Special stuff that may be needed by specific included code units is done here.
  call Grid_guardCellMaskHook(gcell_on_cc)

  !! now handle other situations that may arise when density is included
  !! in the simulation
  if(dens) then
     if(.not.gcell_on_cc(DENS_VAR)) then
        if (gr_convertToConsvdForMeshCalls .OR. gr_convertToConsvdInMeshInterp) then
           do iref=1,NUNK_VARS
              !! For mass-specific variable u, interpolation may be done on the
              !! product u*rho, so density is needed, too.
              gcell_on_cc(DENS_VAR)=gcell_on_cc(DENS_VAR).or.&
                   (gcell_on_cc(iref).and.(gr_vartypes(iref)==VARTYPE_PER_MASS))
           end do
        end if
     end if
  endif

#ifdef GRID_WITH_MONOTONIC

  if (SPECIES_BEGIN .LT. SPECIES_END) then
     if (gr_convertToConsvdForMeshCalls .OR. gr_convertToConsvdInMeshInterp) then
        if (dens) then
           if(gcell_on_cc(DENS_VAR)) gcell_on_cc(SPECIES_BEGIN:SPECIES_END) = .TRUE.
        end if
     else
        if( any(gcell_on_cc(SPECIES_BEGIN:SPECIES_END)))&
             gcell_on_cc(SPECIES_BEGIN:SPECIES_END) = .TRUE.
     end if
  end if

#endif
end subroutine gr_makeMaskConsistent
