!!****if* source/Simulation/SimulationMain/incompFlow/FlowBoiling/IO_readUserArray
!! NOTICE
!!  Copyright 2023 UChicago Argonne, LLC and contributors
!!
!!  Licensed under the Apache License, Version 2.0 (the "License");
!!  you may not use this file except in compliance with the License.
!!
!! NAME
!!  IO_readUserArray
!!
!! SYNOPSIS
!!  call IO_readUserArray()
!!
!! DESCRIPTION
!!  Restores the Heater unit's restart state (lumped-capacitance wall temperature)
!!  from the checkpoint file. See IO/IO_readUserArray for the generic description.
!!***
subroutine IO_readUserArray()
   use Heater_interface, ONLY: Heater_readCheckpoint
   implicit none
   call Heater_readCheckpoint()
end subroutine IO_readUserArray
