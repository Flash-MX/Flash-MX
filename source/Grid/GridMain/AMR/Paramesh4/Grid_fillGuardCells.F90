!!****if* source/Grid/GridMain/AMR/Paramesh4/Grid_fillGuardCells
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
!! NAME
!!  Grid_fillGuardCells
!!
!! SYNOPSIS
!!
!!  call Grid_fillGuardCells(integer(IN) :: gridDataStruct,
!!                           integer(IN) :: idir,
!!                  optional,integer(IN) :: minLayers,
!!                  optional,integer(IN) :: maskSize,
!!                  optional,logical(IN),dimension(:) :: mask(maskSize),
!!                  optional,logical(IN) :: makeMaskConsistent,
!!                  optional,logical(IN) :: doLogMask,
!!                  optional,integer(IN) :: selectBlockType,
!!                  optional,logical(IN) :: unitReadsMeshDataOnly)
!!
!! DESCRIPTION
!!
!!  This routine fills the guardcells of the specified data structure of 
!!  each block present in the mesh. If the adjacent blocks are at the same
!!  level of refinement, then the values are copied from the appropriate
!!  internal cells of the neighboring block. If the blocks are at different
!!  levels of refinement, then in addition to copying, there will be 
!!  restriction or prolongation.
!!
!!
!!  The argument "gridDataStruct" can take one of several valid values to determine
!!  a specific grid data structure (or combination of data structures) on which to
!!  apply the guardcell fill operation. The currently available options are listed
!!  with the arguments. Most calls in a typical Flash-X application will use CENTER
!!  as the option, since it is most common to use cell-centered grid data and fill
!!  guardcells for all such variables. When using AMR with Paramesh4, the
!!  subroutine Grid_fillGuardCells can act on an additional cell-centered data
!!  structure provided by Paramesh (by default with space for only a single
!!  variable) represented by the option "WORK". More specialized applications
!!  may want to use other options.
!!  The user can also choose to fill guard cells either in a single direction,
!!  or all of them. For the Flash-X solvers supplied as of 2023,
!!  guard cell are filled in all directions.
!!
!! ARGUMENTS 
!!  
!!
!!  gridDataStruct - integer constant, defined in "constants.h", indicating for
!!                   which grid data structures the guard cells need to be filled.
!!
!!                   Paramesh has 5 data structures for grid variables, the first
!!                   four store the physical variables defined on the mesh. The
!!                   fifth one includes by default a single variable.
!!
!!                   unk                cell centered,
!!                   facex,facey,facez  face centered along i,j,k 
!!                                      direction, respectively,
!!                   work               cell centered, single variable.
!!                   
!!                   valid values of gridDataStruct are  
!!                   CENTER             unk only
!!                   WORK               work   (only supported with Paramesh4 Grid)
!!                   FACEX              facex  (only supported with Paramesh4 and UG)
!!                   FACEY              facey  (only supported with Paramesh4 and UG)
!!                   FACEZ              facez  (only supported with Paramesh4 and UG)
!!                   FACES              facex,facey, and facez
!!                   CENTER_FACES       unk and facex,facey,facez
!!
!!  idir - direction of guardcell fill.  User can specify ALLDIR for all (x,y,z)
!!         directions, or if, for example, the algorithm only does one directional
!!         sweep at a time then time can be saved by filling only the guardcell
!!         direction that is needed.  A user would pass in the constants defined
!!         in constants.h IAXIS, JAXIS or KAXIS to fill guardcells in only one 
!!         direction.        
!!         All layers of guardcells in the given direction(s) are filled if one
!!         of IAXIS, JAXIS, or KAXIS is specified, or if ALLDIR is specified
!!         and minLayers (see below) is not present.
!!
!!  minLayers - minimum number of guardcell layers requested for all directions.
!!              The caller requests at least this many layers of
!!              guardcells to be filled.  If idir is given as one of IAXIS,
!!              JAXIS, or KAXIS, this applies to any directions NOT selected by
!!              idir. On the other hand, if idir is given as ALLDIR, then
!!              minLayers appliers to all directions equally.
!!              If not specified, the default is 0 if idir is given as IAXIS,
!!              JAXIS, or KAXIS, meaning no guardcells need to be filled in for
!!              the directions perpendicular to what idir selects; the default
!!              is NGUARD, the full number of available guardcells, if idir
!!              is ALLDIR.
!!              Note that the caller can specify, using minLayers, how many
!!              layers it needs filled, but the implementation may do
!!              more and actually fill all or some additional layers.
!!              The caller must therefore not rely on some guardcells
!!              remaining unchanged.
!!
!!  maskSize - the size of the mask array. 
!! 
!!  mask -  It is a one-dimensional logical array 
!!          with indices corresponding to variables in the grid data
!!          structures. If a variable should have its guardcells filled,
!!          the corresponding element in "mask" is true, otherwise it is
!!          false.
!!          The mask is always ignored if the runtime parameter
!!          enableMaskedGCFill is set .FALSE.
!!
!!  selectBlockType - selects the blocks whose guard cells must be filled
!!            by block type.
!!
!!              This argument is ignored in UG Implementations.
!!
!!              For PARAMESH Grid implementations, recognized values are :
!!
!!              ALL_BLKS    all local blocks on a processor.
!!                          This is not valid in all PARAMESH versions.
!!
!!              ACTIVE_BLKS all currently active blocks, in the PARAMESH
!!                          context this means parent and leaf blocks,
!!                          that is, blocks whose node type is 1 or 2,
!!                          but not blocks of node type 3 (ANCESTOR).
!!              
!!              LEAF        only LEAF blocks, i.e., blocks whose PARAMESH
!!                          node type is 1
!!            
!!              These constants are defined in constants.h
!!
!!       Note that if advance_all_levels is set (in a PARAMESH version
!!       that implements this global flag), guard cells in all levels of
!!       blocks are filled anyway.
!!
!!       Note that the caller can specify, using selectBlockType, which
!!       blocks it needs filled, but the implementation may do
!!       more and actually fill guard cells in additional blocks.
!!       The caller must therefore not rely on guardcells
!!       in other blocks remaining unchanged.
!!
!! unitReadsMeshDataOnly - specifies that the unit calling Grid_fillGuardCells
!!                         will not update any internal grid data after the call;
!!                         or, if it does, it will notify the Grid unit of it
!!                         by calling Grid_notifySolnDataUpdate later.
!!                         This protocol allows the NEXT call of
!!                         Grid_fillGuardCells to skip the actual communication
!!                         when it detects that the guard cells already contain
!!                         up to date data.
!!
!! EXAMPLE 
!!
!!   #include "Simulation.h"
!!   #include "constants.h"
!!
!!      call Grid_fillGuardCells( CENTER, IAXIS)
!!
!!     This call will fill all guardcells for all cell-centered 
!!     variables in the x direction.
!!     
!! EXAMPLE 2
!!
!!   #include "Simulation.h"
!!   #include "constants.h"
!!
!!      call Grid_fillGuardCells( WORK, ALLDIR)
!!     
!!     This call fills guardcells along all directions. The operation is applied
!!     to the WORK data structure available in paramesh only.
!!
!! SIDE EFFECTS
!!
!!  After this function returns, all parents of leaf blocks will have current and 
!!  valid solution data (at least for the variables determined by the gridDataStruct
!!  and mask dummy arguments). This is because amr_guardcell calls amr_restrict
!!  internally.
!!
!! NOTES
!!
!!  In the default mode, this routine fills guardcells of all the variables
!!  in the specified data structure. However, if masking is used
!!  it is possible to fill guardcells of only 
!!  selected variables. The users must exercise a great deal of caution in 
!!  using masking in the guardcell filling, since masking out some variables may
!!  have unintended consequences.  For example, if any conserved variable
!!  is set to true in the mask, density must be true, otherwise the interpolated
!!  values of the the conserved variable at fine-coarse boundaries will be 
!!  wrong. It is highly recommended that the argument makeMaskConsistent be set to 
!!  true when using masking, since that provides error checking for
!!  the variable sets included in the released solvers. However,  
!!  these checks may not be enough for new solvers introduced by the users.
!!
!!  This function, or one of the lower-level functions invoked by it, MUST
!!  be called (with updated solution data) before child blocks may be removed
!!  in the course of derefinement! See side effects, above, for the reason.
!!
!! 
!!***

#ifdef DEBUG_ALL
#define DEBUG_GRID
#endif

#include "constants.h"
#include "Simulation.h"

subroutine Grid_fillGuardCells(gridDataStruct, idir, &
     minLayers, maskSize, mask, makeMaskConsistent,&
     doLogMask,selectBlockType,unitReadsMeshDataOnly)

  use Grid_data, ONLY :  gr_justExchangedGC, &
        gr_meshMe, gr_meshComm, &
       gr_gcellsUpToDate,gr_convertToConsvdInMeshInterp
  use gr_specificData, ONLY : gr_enableMaskedGCFill
  use Logfile_interface, ONLY : Logfile_stampMessage, Logfile_stampVarMask
  use Driver_interface, ONLY : Driver_abort
  use Timers_interface, ONLY : Timers_start, Timers_stop
  use Grid_interface, ONLY : Grid_getTileIterator, &
                             Grid_releaseTileIterator
  use gr_interface, ONLY : gr_setGcFillNLayers
  use paramesh_dimensions, ONLY : l2p5d,ndim
  use physicaldata, ONLY : gcell_on_cc,gcell_on_fc, no_permanent_guardcells
  use paramesh_interfaces, ONLY : amr_guardcell, amr_restrict
  use paramesh_mpi_interfaces, ONLY: mpi_amr_comm_setup
  use Grid_iterator, ONLY : Grid_iterator_t
  use Grid_tile,     ONLY : Grid_tile_t

#include "Flashx_mpi_implicitNone.fh"

  integer, intent(in) :: gridDataStruct
  integer, intent(in) :: idir
  integer, optional,intent(in) :: minLayers
  integer, optional, intent(IN) :: maskSize
  logical, optional, dimension(:),intent(IN) :: mask
  logical, optional,intent(IN) :: makeMaskConsistent
  logical, optional,intent(IN) :: doLogMask
  integer, optional,intent(IN) :: selectBlockType
  logical, optional, intent(IN) :: unitReadsMeshDataOnly
  
  integer :: iopt,guard, i,offset
  integer,dimension(MDIM) :: layers, returnLayers
  integer :: maxNodetype_gcWanted
  integer :: nlayers_transverse
  integer :: listBlockType
  real,dimension(:,:,:,:),pointer::solnData
  type(Grid_iterator_t) :: itor
  type(Grid_tile_t)     :: tileDesc

  logical :: lcc, lfc, lec, lnc, lguard, lprolong, lflux, ledge, lrestrict, lfulltree
  integer :: ierr


  logical, save :: maskWarningDone = .FALSE.
  logical :: skipThisGcellFill, skipNextGcellFill
  character(len=10) :: tagext


#ifdef DEBUG_GRID
  logical:: validDataStructure,validMaskSize
  validDataStructure = (gridDataStruct==CENTER).or.&
                       (gridDataStruct==FACES).or.&
                       (gridDataStruct==FACEX).or.&
                       (gridDataStruct==FACEY).or.&
                       (gridDataStruct==FACEZ).or.&
                       (gridDataStruct==WORK).or.&
                       (gridDataStruct==CENTER_FACES)
  if(.not.validDataStructure)then
     call Driver_abort("GCfill: invalid data structure")
  end if

#endif

  nullify(solnData)

  !We can skip this guard cell fill if the guard cells are up to date.
  if (gridDataStruct /= WORK) then
     skipThisGcellFill = gr_gcellsUpToDate
  else
     skipThisGcellFill = .false.
  end if


  if (ndim<2) gcell_on_fc(KAXIS,:) = .false.

  if (.NOT. gr_enableMaskedGCFill) then

     !! If masking is disabled then a warning is issued and all masking related
     !! processing is skipped

     if (.NOT. maskWarningDone) then
        call Logfile_stampMessage( 'INFO: Grid_fillGuardCells is ignoring masking.')
        if (gr_meshMe==MASTER_PE) print*,    'INFO: Grid_fillGuardCells is ignoring masking.'
        maskWarningDone = .TRUE.
     end if

  else
     
     !! if masking is not explicitly disabled then the presence of a mask allows 
     !! masking to proceed

     if(present(mask))then
        if(present(maskSize)) then

           !! If both mask and masksize are present, apply the mask
           call gr_setMasks(gridDataStruct,maskSize,mask)
           if(present(makeMaskConsistent))then
              if(makeMaskConsistent) then
                 !! if the caller routine is asking for a consistency check
                 !! then mask may be modified
                 call gr_makeMaskConsistent(gridDataStruct)
              end if
           end if
        else  !! if mask is present without the maskSize, abort
           call Driver_abort("gcfill :: maskSize must be present with mask")
        end if
     end if
  end if
  
  !! if guardcells were just exchanged, don't do it again!
  !!if (gr_justExchangedGC) return
!!$  if (.not. skipThisGcellFill) then
!!$     call Timers_start("guardcell Barrier")
!!$     call MPI_BARRIER(gr_meshComm, ierr)
!!$     call Timers_stop("guardcell Barrier")
!!$  end if
  call Timers_start("guardcell internal")
  !! appropriately mask the data structures to ensure that only the correct data
  !! structure is filled.
  if((gridDataStruct/=CENTER_FACES).and.(gridDataStruct/=CENTER))gcell_on_cc = .false.
  if(gridDataStruct==CENTER)gcell_on_fc=.false.
  if(gridDataStruct==FACEX)gcell_on_fc(JAXIS:KAXIS,:)=.false.
  if(gridDataStruct==FACEY)then
     gcell_on_fc(IAXIS,:)=.false.
     gcell_on_fc(KAXIS,:)=.false.
  end if
  if(gridDataStruct==FACEZ)gcell_on_fc(IAXIS:JAXIS,:)=.false.
  
  if(present(mask))then
     if(present(maskSize)) then
        if (present(doLogMask)) then
           if (doLogMask) then
              if (skipThisGcellFill) then
                 tagext = '(skipped)'
              else
                 tagext = ''
              end if
              call Logfile_stampVarMask(gcell_on_cc, '[Grid_fillGuardCells]'//tagext, 'gcSet')
           end if
        end if
     end if
  end if

  guard = NGUARD
  
  iopt = 1
  if(gridDataStruct==WORK)iopt = 2
  
  ! If called for WORK, at this point
  ! - mask will be completely ignored (including its presence or absence)
  ! - the gcell_on_{cc,fc} arrays will not be modified. - KW
  
  listBlockType = ACTIVE_BLKS
  
  !----------------------------------------------------------------
  ! Figure out nlayers arguments to amr_guardcell based on our arguments
  call gr_setGcFillNLayers(layers, idir, guard, minLayers, returnLayers)

  if (no_permanent_guardcells) then

     ! We don't really need this according to K.O., since it is included in amr_restrict
     ! as long as we don't use the mode in which all tree levels are always propagated in
     ! time and kept always valid. - KW
     call amr_1blk_copy_soln(-1)
     
     iopt = 1
     call amr_restrict(gr_meshMe, iopt, 1)
     call gr_commSetUp(gridDataStruct)
     layers(:) = guard
  else
     if (present(selectBlockType)) then
        listBlockType = selectBlockType
        select case (selectBlockType)
        case(LEAF)
           maxNodetype_gcWanted = 1
        case(ACTIVE_BLKS)
           maxNodetype_gcWanted = 2
        case(ALL_BLKS)
           call Driver_abort('Grid_fillGuardCells: unsupported value ALL_BLKS for selectBlockType!')
#ifdef DEBUG_GRID
        case default
           call Driver_abort('Grid_fillGuardCells: unrecognized value for selectBlockType!')
#endif
        end select
     else
        maxNodetype_gcWanted = -1 !by default, old behavior (as in PARAMESH 4.0 as distributed)
     end if

     if((gridDataStruct==CENTER_FACES).or.(gridDataStruct==CENTER)) then
        if (.not. skipThisGcellFill) then
           call Grid_getTileIterator(itor, listBlockType, tiling=.FALSE.)
           do while (itor%isValid())
              call itor%currentTile(tileDesc)
              call gr_primitiveToConserve(tileDesc)

              call itor%next()
           end do
           call Grid_releaseTileIterator(itor)
        end if
     end if
 

     if (.not. skipThisGcellFill) then
        if (gr_convertToConsvdInMeshInterp) then
           !   call gr_sanitizeDataAfterInterp(listBlockType, 'BEFORE gc filling', layers)
        end if
        !call amr_restrict(gr_meshMe, 1, 0, .true.)
        if (gr_convertToConsvdInMeshInterp) then
           !   call gr_sanitizeDataAfterInterp(listBlockType, 'BEFORE gc filling, after restrict', layers)
        end if

#ifdef DEBUG_GRID
        print*, 'amr_guardcell(PE', iopt, guard,layers,')'
#endif
        call Timers_start("amr_guardcell")
        call amr_guardcell(gr_meshMe, iopt, guard,layers(IAXIS),layers(JAXIS),layers(KAXIS),&
             maxNodetype_gcWanted=maxNodetype_gcWanted)
        call Timers_stop("amr_guardcell")
        call gr_freeCommRecvBuffer
     end if

     if ((gridDataStruct==CENTER_FACES).or.(gridDataStruct==CENTER)) then
        if (.not. skipThisGcellFill) then
            call Grid_getTileIterator(itor, listBlockType, tiling=.FALSE.)
            do while (itor%isValid())
                call itor%currentTile(tileDesc)
                call gr_conserveToPrimitive(tileDesc, .TRUE.)

                call itor%next()
            end do
            call Grid_releaseTileIterator(itor)

            if (gr_convertToConsvdInMeshInterp) then
               call gr_sanitizeDataAfterInterp(listBlockType, 'after gc filling', layers)
            end if
        end if
     end if
 
     gr_justExchangedGC = .true.
     
  end if

  if (iopt == 1) then
     ! Reset the global gcell_on_cc and gcell_on_fc to their defaults.
     ! This seems to be needed, otherwise the behavior of PARAMESH routines
     ! called elsewhere is changed. - KW
     gcell_on_cc = .true.
     gcell_on_fc = .true.
     if (ndim==2 .AND. l2p5d==1) gcell_on_fc(KAXIS,:) = .false.
  end if



  !We now test whether we can skip the next guard cell fill.
  skipNextGcellFill = .false.
  if(present(unitReadsMeshDataOnly)) then
     if (unitReadsMeshDataOnly) then
        if (gr_gcellsUpToDate) then
           !If *all* guard cells were up to date on entry to
           !Grid_fillGuardCells then they will continue to be up to date.
           skipNextGcellFill = .true.
        else
           !Check whether we filled guardcells for all layers, all
           !variables and all active blocks.  This ensures all
           !guard cells are up to date for the next unit.
           if ((gridDataStruct == CENTER_FACES .OR. &
                (gridDataStruct == CENTER .AND. (NFACE_VARS < 1))) &
                .and. idir == ALLDIR) then
              skipNextGcellFill = .true.
              if (present(minLayers)) then
                 if (minval(layers(1:NDIM)) < guard) then
                    skipNextGcellFill = .false.
                 end if
              end if
              if (present(mask)) then
                 if (.not.all(mask .eqv. .true.)) then
                    skipNextGcellFill = .false.
                 end if
              end if
              if (present(selectBlockType)) then
                 if (selectBlockType /= ACTIVE_BLKS) then
                    skipNextGcellFill = .false.
                 end if
              end if
           end if
        end if
     end if
  end if
  gr_gcellsUpToDate = skipNextGcellFill


  call Timers_stop("guardcell internal")

end subroutine Grid_fillGuardCells
