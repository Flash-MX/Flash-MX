!!****f* source/physics/sourceTerms/Heater/Heater_updateLumped
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
!!  Stub. See HeaterMain/Heater_updateLumped for the lumped-capacitance heater.
!!***
#include "constants.h"
#include "Simulation.h"

subroutine Heater_updateLumped(dt, stime)
   implicit none
   real, intent(in) :: dt, stime
end subroutine Heater_updateLumped
