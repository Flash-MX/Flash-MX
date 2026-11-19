!!****if* source/physics/sourceTerms/Heater/HeaterMain/Heater_updateLumped
!! NOTICE
!!  Copyright 2023 UChicago Argonne, LLC and contributors
!!
!!  Licensed under the Apache License, Version 2.0 (the "License");
!!  you may not use this file except in compliance with the License.
!!
!! NAME
!!  Heater_updateLumped
!!
!! SYNOPSIS
!!  call Heater_updateLumped(real(IN) :: dt, real(IN) :: stime)
!!
!! DESCRIPTION
!!  Lumped-capacitance (isothermal) heater, active when htr_lumpedFlg is true.
!!  The heater is a block of uniform temperature heater%wallTemp, used by
!!  Heater_applyBCToRegion as a Dirichlet wall temperature (heatFluxFlg and
!!  varTempFlg are forced to false in Heater_init). Each step the temperature
!!  advances from the energy balance between the imposed heat flux and the heat
!!  the fluid actually removes at the wall:
!!
!!     htr_lumpedCapacity * d(wallTemp)/dt = heater%heatFlux - <q_removed>
!!
!!  <q_removed> is the area average over the heater of
!!     k_phase * (wallTemp - T_1) / (dy/2),
!!  T_1 the first interior cell, k_phase = 1 in liquid and mph_thcoGas in vapor
!!  (the same conductivity switch the heat-flux BC uses). Everything is in the
!!  solver's nondimensional units: flux in k_l*dT/lc, so htr_lumpedCapacity is
!!  (rho c delta)_heater * lc / (k_l * tc). Physical heaters (mm of copper) give
!!  ~1e4, i.e. a wall temperature that barely moves within a run; a smaller value
!!  (default 100) relaxes the wall to the balance point within a few time units.
!!  The master rank prints Twall, the imposed and removed flux and the wetted
!!  fraction every step. wallTemp is kept in the checkpoint scalars (htr_wallTemp_<n>)
!!  and restored by Heater_readCheckpoint on a restart; htr_lumpedWallTemp overrides
!!  it when set.
!!
!! ARGUMENTS
!!  dt    - current time step
!!  stime - current simulation time (after the step increment)
!!
!! NOTES
!!  The REORDER directive below is required: with -index-reorder (+amrex) the
!!  setup script rewrites solnData(VAR, i, j, k) to the (i, j, k, VAR) layout
!!  only in files that carry it; without it the reads land in the wrong memory.
!!***
!!REORDER(4): solnData
#include "constants.h"
#include "Simulation.h"

subroutine Heater_updateLumped(dt, stime)

   use Heater_data
   use Heater_type, ONLY: Heater_type_t
   use Grid_interface, ONLY: Grid_getTileIterator, Grid_releaseTileIterator
   use Grid_iterator, ONLY: Grid_iterator_t
   use Grid_tile, ONLY: Grid_tile_t
   use Timers_interface, ONLY: Timers_start, Timers_stop
   use IO_interface, ONLY: IO_setScalar

   implicit none
   include "Flashx_mpi.h"

   real, intent(in) :: dt, stime

   type(Grid_iterator_t) :: itor
   type(Grid_tile_t) :: tileDesc
   type(Heater_type_t), pointer :: heater
   real, pointer, dimension(:, :, :, :) :: solnData
   real, dimension(LOW:HIGH, MDIM) :: bndBox
   real, dimension(MDIM) :: del
   real, allocatable, dimension(:) :: loc, glb
   real :: xc, zc, dA, thco, qRem, wet, tol
   integer :: i, j, k, htr, ierr
   logical :: bottom
   character(len=24) :: sname

   if (.not. htr_lumpedFlg) return

   call Timers_start("Heater_updateLumped")

   allocate (loc(3*htr_numHeaters), glb(3*htr_numHeaters))
   loc = 0.0
   glb = 0.0

   nullify (solnData)
   call Grid_getTileIterator(itor, nodetype=LEAF, tiling=.FALSE.)
   do while (itor%isValid())
      call itor%currentTile(tileDesc)
      call tileDesc%deltas(del)
      call tileDesc%boundBox(bndBox)
      call tileDesc%getDataPtr(solnData, CENTER)

      do htr = 1, htr_numHeaters
         heater => htr_heaterInfo(htr)

         ! which wall carries this heater (same test as Heater_applyBCToRegion)
         bottom = abs(0.5*(heater%yMax+heater%yMin)-htr_yMin) .lt. &
                  abs(0.5*(heater%yMax+heater%yMin)-htr_yMax)
         tol = 0.01*del(JAXIS)
         if (bottom) then
            if (abs(bndBox(LOW, JAXIS)-htr_yMin) .gt. tol) cycle
            j = tileDesc%limits(LOW, JAXIS)
         else
            if (abs(bndBox(HIGH, JAXIS)-htr_yMax) .gt. tol) cycle
            j = tileDesc%limits(HIGH, JAXIS)
         end if

         dA = del(IAXIS)
#if NDIM == MDIM
         dA = dA*del(KAXIS)
#endif
         do k = tileDesc%limits(LOW, KAXIS), tileDesc%limits(HIGH, KAXIS)
#if NDIM == MDIM
            zc = bndBox(LOW, KAXIS)+(k-tileDesc%limits(LOW, KAXIS)+0.5)*del(KAXIS)
            if (zc .le. heater%zMin .or. zc .ge. heater%zMax) cycle
#endif
            do i = tileDesc%limits(LOW, IAXIS), tileDesc%limits(HIGH, IAXIS)
               xc = bndBox(LOW, IAXIS)+(i-tileDesc%limits(LOW, IAXIS)+0.5)*del(IAXIS)
               if (xc .le. heater%xMin .or. xc .ge. heater%xMax) cycle

               if (solnData(DFUN_VAR, i, j, k) .le. 0.0) then
                  thco = 1.0
                  loc(3*htr) = loc(3*htr)+dA                       ! wetted area
               else
                  thco = htr_thcoGas
               end if
               loc(3*htr-2) = loc(3*htr-2)+ &
                              thco*2.0*(heater%wallTemp-solnData(TEMP_VAR, i, j, k))/del(JAXIS)*dA
               loc(3*htr-1) = loc(3*htr-1)+dA                      ! heater area seen by this rank
            end do
         end do
      end do

      call tileDesc%releaseDataPtr(solnData, CENTER)
      call itor%next()
   end do
   call Grid_releaseTileIterator(itor)

   call MPI_Allreduce(loc, glb, 3*htr_numHeaters, FLASH_REAL, MPI_SUM, htr_meshComm, ierr)

   do htr = 1, htr_numHeaters
      heater => htr_heaterInfo(htr)
      if (glb(3*htr-1) .gt. 0.0) then
         qRem = glb(3*htr-2)/glb(3*htr-1)
         wet = glb(3*htr)/glb(3*htr-1)
      else
         qRem = 0.0
         wet = 0.0
      end if
      heater%wallTemp = heater%wallTemp+dt*(heater%heatFlux-qRem)/htr_lumpedCapacity
      ! keep the wall temperature in the checkpoint scalars (restored by Heater_readCheckpoint)
      write (sname, '(A,I0)') 'htr_wallTemp_', htr
      call IO_setScalar(trim(sname), heater%wallTemp)

      if (htr_meshMe .eq. MASTER_PE) &
         write (*, '(A,I2,A,g14.6,A,g14.6,A,g14.6,A,f7.4,A,g14.6)') &
         ' Lumped heater', htr, ': Twall=', heater%wallTemp, ' qApp=', heater%heatFlux, &
         ' qRem=', qRem, ' wet=', wet, ' t=', stime
   end do

   deallocate (loc, glb)

   call Timers_stop("Heater_updateLumped")

end subroutine Heater_updateLumped
