# Related open-source projects

Drone Scout is a *planning-level* simulator with a point-mass aircraft and an uncalibrated power model. To move from this to physical validation (see report Chapter 17), these are the usual open-source building blocks. They are listed for orientation; none of their code is included here. Licences were read from each project's GitHub page on 25 October 2026.

| Project | Maintainer | Licence | Useful for |
|---|---|---|---|
| [PX4 Autopilot](https://github.com/PX4/PX4-Autopilot) | Dronecode Foundation (Linux Foundation project) | BSD-3-Clause | Real flight control and flight logs to calibrate the power and controller model |
| [ArduPilot](https://github.com/ArduPilot/ardupilot) | ArduPilot project | GPL-3.0 | Autopilot with survey-grid missions and detailed logs |
| [QGroundControl](https://github.com/mavlink/qgroundcontrol) | MAVLink / Dronecode | Apache-2.0 and GPL-3.0 (dual) | Ground station that can export survey plans for comparison with this planner |
| [Gazebo Sim](https://github.com/gazebosim/gz-sim) | Intrinsic / Open Robotics community | Apache-2.0 | Physics-based 3-D simulation to replace the point-mass model |
| [WebODM](https://github.com/OpenDroneMap/WebODM) | OpenDroneMap community | AGPL-3.0 | Photogrammetric reconstruction to test whether nominal overlap is *sufficient* overlap |
| [FIELDimageR](https://github.com/OpenDroneMap/FIELDimageR) | OpenDroneMap / UW-Madison authors | GPL-2.0 | Plot extraction and vegetation indices from orthomosaics |

## Manufacturer information

- **DJI**: reference airframe values were taken from public specifications of the Phantom 4 Multispectral. DJI's SDKs and apps are proprietary and are not used or redistributed here.

## Open data

- [ADD256](https://github.com/thsant/add256) (apples, CC BY-NC 4.0), [CoFly-WeedDB](https://github.com/CoFly-Project/CoFly-WeedDB) (weeds), [CADI-AI](https://github.com/karaagro/cadi-ai) (cashew). Check each licence before use; see [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Integrating your own data

`FieldMap.from_array(raster, width_m, height_m)` accepts any 0-100 canopy or index raster, for example an orthomosaic derivative exported from FIELDimageR or WebODM. You are responsible for the licence of data you load.
