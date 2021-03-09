#!/usr/bin/env python3
#
# Copyright (c) 2020 LG Electronics, Inc.
#
# This software contains code licensed as described in LICENSE.
#

from datetime import datetime
from environs import Env
import random
import lgsvl

'''
LGSVL__AUTOPILOT_0_HOST             IP address of the computer running the bridge to connect to
LGSVL__AUTOPILOT_0_PORT             Port that the bridge listens on for messages
LGSVL__AUTOPILOT_0_VEHICLE_CONFIG   Vehicle configuration to be loaded in Dreamview (Capitalization and spacing must match the dropdown in Dreamview)
LGSVL__AUTOPILOT_HD_MAP             HD map to be loaded in Dreamview (Capitalization and spacing must match the dropdown in Dreamview)
LGSVL__MAP                          ID of map to be loaded in Simulator
LGSVL__RANDOM_SEED                  Simulation random seed
LGSVL__SIMULATION_DURATION_SECS     How long to run the simulation for
LGSVL__SIMULATOR_HOST               IP address of computer running simulator (Master node if a cluster)
LGSVL__SIMULATOR_PORT               Port that the simulator allows websocket connections over
LGSVL__VEHICLE_0                    ID of EGO vehicle to be loaded in Simulator
'''

env = Env()

SIMULATOR_HOST = env.str("LGSVL__SIMULATOR_HOST", "127.0.0.1")
SIMULATOR_PORT = env.int("LGSVL__SIMULATOR_PORT", 8181)
BRIDGE_HOST = env.str("LGSVL__AUTOPILOT_0_HOST", "127.0.0.1")
BRIDGE_PORT = env.int("LGSVL__AUTOPILOT_0_PORT", 9090)

# Map name is passed to WISE instead ID by default.
LGSVL__MAP = env.str("LGSVL__MAP", "san_francisco")
# Here we intentionally make a typo in envrionment variable name and
# use LGSVL__VEHICLE_1 instead of LGSVL__VEHICLE_0 because
# otherwise it will receive proper vehicle ID and simulator will fail,
# since IDs are not supported yet. So for now it will fail to read
# environment variable and use vehicle name as backup option
# Default vehicle for this test case is Lincoln2017MKZ - Apollo 5.0 (modular testing)
# https://wise.svlsimulator.com/vehicles/profile/73805704-1e46-4eb6-b5f9-ec2244d5951e/edit/configuration/5c7fb3b0-1fd4-4943-8347-f73a05749718
DEFAULT_VEHICLE_CONFIG = "5c7fb3b0-1fd4-4943-8347-f73a05749718"
LGSVL__VEHICLE_0 = env.str("LGSVL__VEHICLE_0", DEFAULT_VEHICLE_CONFIG)
LGSVL__AUTOPILOT_HD_MAP = env.str("LGSVL__AUTOPILOT_HD_MAP", "SanFrancisco")
LGSVL__AUTOPILOT_0_VEHICLE_CONFIG = env.str("LGSVL__AUTOPILOT_0_VEHICLE_CONFIG", 'Lincoln2017MKZ')
LGSVL__SIMULATION_DURATION_SECS = 120.0
LGSVL__RANDOM_SEED = env.int("LGSVL__RANDOM_SEED", 51472)

sim = lgsvl.Simulator(SIMULATOR_HOST, SIMULATOR_PORT)
try:
    print("Loading map {}...".format(SIMULATOR_MAP))
    sim.load(SIMULATOR_MAP, LGSVL__RANDOM_SEED) # laod map with random seed
except Exception:
    if sim.current_scene == SIMULATOR_MAP:
        sim.reset()
    else:
        sim.load(SIMULATOR_MAP)


# reset time of the day
sim.set_date_time(datetime(2020, 7, 1, 15, 0, 0, 0), True)

spawns = sim.get_spawn()
# select spawn deterministically depending on the seed
spawn_index = LGSVL__RANDOM_SEED % len(spawns)

state = lgsvl.AgentState()
state.transform = spawns[spawn_index]  # TODO some sort of Env Variable so that user/wise can select from list
print("Loading vehicle {}...".format(LGSVL__VEHICLE_0))
ego = sim.add_agent(LGSVL__VEHICLE_0, lgsvl.AgentType.EGO, state)

print("Connecting to bridge...")
# The EGO is now looking for a bridge at the specified IP and port
ego.connect_bridge(BRIDGE_HOST, BRIDGE_PORT)

def on_collision(agent1, agent2, contact):
    raise Exception("{} collided with {}".format(agent1, agent2))
    sys.exit()

ego.on_collision(on_collision)

dv = lgsvl.dreamview.Connection(sim, ego, BRIDGE_HOST)
dv.set_hd_map(LGSVL__AUTOPILOT_HD_MAP)
dv.set_vehicle(LGSVL__AUTOPILOT_0_VEHICLE_CONFIG)

destination_index = LGSVL__RANDOM_SEED % len(spawns[spawn_index].destinations)
destination = spawns[spawn_index].destinations[destination_index] # TODO some sort of Env Variable so that user/wise can select from list

default_modules = [
    'Localization',
    'Transform',
    'Routing',
    'Prediction',
    'Planning',
    'Control',
    'Recorder'
]

dv.disable_apollo()
dv.setup_apollo(destination.position.x, destination.position.z, default_modules)

print("adding npcs")
sim.add_random_agents(lgsvl.AgentType.NPC)
sim.add_random_agents(lgsvl.AgentType.PEDESTRIAN)

sim.run(LGSVL__SIMULATION_DURATION_SECS)
