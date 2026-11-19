!!****if* source/physics/sourceTerms/Heater/HeaterMain/Heater_readCheckpoint
!! NOTICE
!!  Copyright 2023 UChicago Argonne, LLC and contributors
!!
!!  Licensed under the Apache License, Version 2.0 (the "License");
!!  you may not use this file except in compliance with the License.
!!
!! NAME
!!  Heater_readCheckpoint
!!
!! SYNOPSIS
!!  call Heater_readCheckpoint()
!!
!! DESCRIPTION
!!  Restores the heater state saved in a checkpoint: the lumped-capacitance wall
!!  temperature (checkpoint scalar htr_wallTemp_<n>, set by Heater_updateLumped),
!!  unless the runtime parameter htr_lumpedWallTemp overrides it. A checkpoint
!!  without the scalar (older run, or htr_lumpedFlg off when it was written) leaves
!!  the heater file value in place.
!!
!!  Must be called from IO_readUserArray: Heater_init runs before the checkpoint
!!  scalars are loaded, so it cannot do this.
!!***
#include "constants.h"
#include "Simulation.h"

subroutine Heater_readCheckpoint()

   use Heater_data, ONLY: htr_lumpedFlg, htr_lumpedWallTemp, htr_numHeaters, htr_heaterInfo, htr_meshMe
   use IO_data, ONLY: io_scalar

   implicit none

   character(len=24) :: sname
   integer :: htr, err
   real    :: rv

   if (.not. htr_lumpedFlg) return
   if (htr_lumpedWallTemp .gt. -1.0e29) return

   do htr = 1, htr_numHeaters
      write (sname, '(A,I0)') 'htr_wallTemp_', htr
      call NameValueLL_getReal(io_scalar, trim(sname), rv, .true., err)
      if (err .eq. NORMAL) then
         htr_heaterInfo(htr)%wallTemp = rv
         if (htr_meshMe .eq. MASTER_PE) write (*, '(A,I2,A,g14.6)') ' Lumped heater', htr, &
            ': wallTemp restored from the checkpoint:', rv
      else if (htr_meshMe .eq. MASTER_PE) then
         write (*, '(A,I2,A,g14.6)') ' Lumped heater', htr, &
            ': no wallTemp in the checkpoint, keeping the heater file value', htr_heaterInfo(htr)%wallTemp
      end if
   end do

end subroutine Heater_readCheckpoint
