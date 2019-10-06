import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.ids.buff_id import BuffId
import random
import math

'''
###################################################################################################
Not very complicated bot, based on basic behaviour with smart ideas from:
Example bots from: (https://github.com/Dentosal/python-sc2)
Beautiful video giude from: (https://www.youtube.com/watch?v=v3LJ6VvpfgI)
Cannon Lover Bot (https://github.com/Hannessa/sc2-bots/tree/master/cannon-lover)
###################################################################################################
TODO:
+ blink micro
+ scouting phoenix 
+ upgrades (shields +, air weapons +, blink +, catapult, ...)
+ cloak detecting (observers)
- mid to end-game tech (tempests + carriers with own micro, mothersip?)
+ darktemplar harassing
+ ability using (voidrays +, high templar?)
- oracle defensive trap?
###################################################################################################
'''

class BronzeCrawler(sc2.BotAI):
    def __init__(self):
        self.MAX_WORKERS = 40
        self.army_count_ground = 0
        self.army_count_air = 0


        ################ DEFS
    ################
    # Approximate army value by adding unit health+shield
    def friendly_army_value(self, position, distance=10):
        value = 0
        for unit in self.units.ready.closer_than(distance, position):
            if unit.can_attack:
                value += unit.health + unit.shield
        return value

    # Approximate army value by adding unit health+shield
    def enemy_army_value_can_attack_ground(self, position, distance=10):
        value = 0
        #couinting only units that can attack
        for unit in self.known_enemy_units.ready.closer_than(distance, position):
            if unit.can_attack and unit.can_attack_ground:
                value += unit.health + unit.shield
                # Add extra army value for marine/marauder, to not under-estimate
                if unit.type_id in [MARINE, MARAUDER]:
                    value += 20
                # Reduce workers in value, to not over-estimate
                if unit.type_id in [DRONE, PROBE, SCV]:
                    value -= 20
        return value

    def enemy_army_value_can_attack_air(self, position, distance=10):
        value = 0
        #couinting only units that can attack
        for unit in self.known_enemy_units.ready.closer_than(distance, position):
            if unit.can_attack and unit.can_attack_air:
                value += unit.health + unit.shield
                # Add extra army value for marine/marauder, to not under-estimate
                if unit.type_id in [MARINE, MARAUDER]:
                    value += 20
                # Reduce workers in value, to not over-estimate
                if unit.type_id in [DRONE, PROBE, SCV]:
                    value -= 20
        return value

    # Count enemy workers around
    def enemy_workers_around(self, position, distance=10):
        enemy_workers = []
        # couinting only workers
        for unit in self.known_enemy_units.ready.closer_than(distance, position):
            if unit.type_id in [DRONE, PROBE, SCV]:
                enemy_workers.append(unit)
        return enemy_workers

    # Define point where gather our units
    def get_rally_location(self):
        if self.units(PYLON).ready.exists:
            rally_location = self.units(PYLON).ready.closest_to(self.game_info.map_center).position
        else:
            rally_location = self.start_location
        return rally_location

    #maybe not needed?
    def get_game_center_random(self, offset_x=50, offset_y=50):
        x = self.game_info.map_center.x
        y = self.game_info.map_center.y
        rand = random.random()
        if rand < 0.2:
            x += offset_x
        elif rand < 0.4:
            x -= offset_x
        elif rand < 0.6:
            y += offset_y
        elif rand < 0.8:
            y -= offset_y
        return sc2.position.Point2((x, y))

    # locate center of the map
    def get_game_center_notrandom(self, offset_x=50, offset_y=50):
        x = self.game_info.map_center.x
        y = self.game_info.map_center.y
        return sc2.position.Point2((x, y))

    # locate good place for our new buildings
    def get_base_build_location(self, base, min_distance=5, max_distance=18):
        return base.position.towards(self.get_game_center_random(), random.randrange(min_distance, max_distance))
        #return base.position.towards(self.get_game_center_notrandom(), random.randrange(min_distance, max_distance))

    # Check if a unit has a specific order. Supports multiple units/targets. Returns unit count.
    def has_order(self, orders, units):
        if type(orders) != list:
            orders = [orders]
        count = 0
        if type(units) == sc2.unit.Unit:
            unit = units
            if len(unit.orders) >= 1 and unit.orders[0].ability.id in orders:
                count += 1
        else:
            for unit in units:
                if len(unit.orders) >= 1 and unit.orders[0].ability.id in orders:
                    count += 1
        return count

    # Check if a unit has a specific target. Supports multiple units/targets. Returns unit count.
    def has_target(self, targets, units):
        if type(targets) != list:
            targets = [targets]
        count = 0
        if type(units) == sc2.unit.Unit:
            unit = units
            if len(unit.orders) == 1 and unit.orders[0].target in targets:
                count += 1
        else:
            for unit in units:
                if len(unit.orders) == 1 and unit.orders[0].target in targets:
                    count += 1
        return count

    # Find target for army to attack
    def find_target(self, state):
        if len(self.known_enemy_units) > 0:  #         if len(self.known_enemy_units) > 0:
            return self.known_enemy_units.closest_to(self.start_location).position
            #return random.choice(self.known_enemy_units.exist)  # exist
        elif len(self.known_enemy_structures) > 0:  # elif len(self.known_enemy_structures) > 0:
            #return random.choice(self.known_enemy_structures.exist)  # exist
            return self.known_enemy_structures.closest_to(self.start_location).position  # exist
        else:
            return self.enemy_start_locations[0]

    # Check if unit has specific ability
    async def has_ability(self, ability, unit):
        abilities = await self.get_available_abilities(unit)
        if ability in abilities:
            return True
        else:
            return False

    # Give an order to unit(s)
    async def order(self, units, order, target=None, silent=True):
        if type(units) != list:
            unit = units
            await self.do(unit(order, target=target))
        else:
            for unit in units:
                await self.do(unit(order, target=target))































    ####################### bot logic by itselt
    #######################

    async def on_step(self, iteration):
        self.iteration = iteration
        self.timemin = self.time/60
        await self.messages()
        await self.distribute_workers()  # built-in function! for probes to return to work after actions
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.handle_chronoboost()
        await self.scout()
        await self.upgrades()

        if self.units(NEXUS).exists:
            if not self.units(NEXUS).amount < self.timemin/4 or self.minerals > 800:  # build offensive buildings and forces only if we have strong...
                # ...economy to not interrupt nexus money (so, force to build additional nexus to nave total of 1 per 3.5 minute)
                await self.army_buildings()
                await self.army_forces()

        #await self.move_army()
        await self.move_army_ground()
        await self.move_army_air()

        await self.darktemplars_actions()
        await self.voidrays_ability()

    ######## MESSAGES
    async def messages(self):
        if self.time % 15 == 0:  # every 15 secs in game time
            await self.chat_send("T:" + str(self.timemin) + "  (minerals)" + \
                                 str(self.state.score.collection_rate_minerals) + "/s  ARMY g/a: " + str(self.army_count_ground) + "/" + str(self.army_count_air))


    ######## PROBES
    async def build_workers(self):
        if self.units(NEXUS).exists:
            nexus = self.units(NEXUS).ready.random
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and len(self.units(PROBE)) < 40:
                abilities = await self.get_available_abilities(nexus)
                if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                    await self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus))
        if (len(self.units(NEXUS)) * 16) > len(self.units(PROBE)) and len(self.units(PROBE)) < (self.MAX_WORKERS + self.timemin) and len(self.units(PROBE)) < 70:
            for nex in self.units(NEXUS).ready.noqueue:
                if self.can_afford(PROBE):
                    await self.do(nex.train(PROBE))

    ######## PYLONS
    async def build_pylons(self):
        if self.supply_left < 4 + self.timemin*2 and self.already_pending(PYLON) < (0 + self.timemin/10) and self.supply_cap < 200:
            nexuses = self.units(NEXUS)
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=self.get_base_build_location(self.units(NEXUS).random, min_distance=4))

    ######## ASSIMILATORS
    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vaspenes = self.state.vespene_geyser.closer_than(12.0, nexus)
            for vaspene in vaspenes:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vaspene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                    await self.do(worker.build(ASSIMILATOR, vaspene))

    ######## EXPAND
    async def expand(self):  # build bases, total 1 + (1 per 3.5 mins)
        if self.units(NEXUS).amount < 1 + self.timemin/4 and self.can_afford(NEXUS) and not self.already_pending(NEXUS):
            await self.expand_now()

    ######## CHRONOBOOST
    async def handle_chronoboost(self):
        if self.units(NEXUS).exists and len(self.units(PROBE)) >= 40:
            nexus = self.units(NEXUS).ready.random
            if await self.has_ability(EFFECT_CHRONOBOOSTENERGYCOST, nexus) and nexus.energy >= 50:
                # Always CB Warpgate research first
                if self.units(CYBERNETICSCORE).ready.exists:
                    cybernetics = self.units(CYBERNETICSCORE).first
                    if not cybernetics.noqueue and not cybernetics.has_buff(CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, cybernetics))
                        return  # Don't CB anything else this step

                # Next, focus on Forge
                if self.units(FORGE).ready.exists:
                    forge = self.units(FORGE).first
                    if not forge.noqueue and not forge.has_buff(CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, forge))
                        return  # Don't CB anything else this step

                # Next, prioritize CB on gates
                for stargate in (self.units(STARGATE).ready):
                    if not stargate.has_buff(CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, stargate))
                        return  # Don't CB anything else this step

                # Next, prioritize CB on gates
                for gateway in (self.units(GATEWAY).ready | self.units(WARPGATE).ready):
                    if not gateway.has_buff(CHRONOBOOSTENERGYCOST):
                        await self.do(nexus(EFFECT_CHRONOBOOSTENERGYCOST, gateway))
                        return  # Don't CB anything else this step




    ######## UPGRADES
    async def upgrades(self):
        #shields - from 6 min
        if self.units(FORGE).ready.noqueue.exists and self.timemin > 6:
            if self.units(FORGE).first.noqueue and self.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL1) and await self.has_ability(FORGERESEARCH_PROTOSSSHIELDSLEVEL1, self.units(FORGE).first):
                await self.do(self.units(FORGE).first(FORGERESEARCH_PROTOSSSHIELDSLEVEL1))
            if self.units(FORGE).first.noqueue and self.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL2) and await self.has_ability(FORGERESEARCH_PROTOSSSHIELDSLEVEL2, self.units(FORGE).first):
                await self.do(self.units(FORGE).first(FORGERESEARCH_PROTOSSSHIELDSLEVEL2))
            if self.units(FORGE).first.noqueue and self.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL3) and await self.has_ability(FORGERESEARCH_PROTOSSSHIELDSLEVEL3, self.units(FORGE).first):
                await self.do(self.units(FORGE).first(FORGERESEARCH_PROTOSSSHIELDSLEVEL3))

        #blink - only if we have stalkers already
        if self.units(TWILIGHTCOUNCIL).ready.noqueue.exists and self.units(STALKER).amount > 2:
            if self.units(TWILIGHTCOUNCIL).first.noqueue and self.can_afford(RESEARCH_BLINK) and await self.has_ability(RESEARCH_BLINK, self.units(TWILIGHTCOUNCIL).first):
                await self.do(self.units(TWILIGHTCOUNCIL).first(RESEARCH_BLINK))

        #air weapons - only if we have air units
        if self.units(CYBERNETICSCORE).ready.noqueue.exists and (self.units(VOIDRAY).amount + self.units(CARRIER).amount + self.units(TEMPEST).amount) > 5:
            if self.units(CYBERNETICSCORE).first.noqueue and self.can_afford(
                    CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1) and await self.has_ability(
                    CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1, self.units(CYBERNETICSCORE).first):
                await self.do(self.units(CYBERNETICSCORE).first(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL1))
            if self.units(CYBERNETICSCORE).first.noqueue and self.can_afford(
                    CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2) and await self.has_ability(
                    CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2, self.units(CYBERNETICSCORE).first):
                await self.do(self.units(CYBERNETICSCORE).first(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL2))
            if self.units(CYBERNETICSCORE).first.noqueue and self.can_afford(
                    CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3) and await self.has_ability(
                    CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3, self.units(CYBERNETICSCORE).first):
                await self.do(self.units(CYBERNETICSCORE).first(CYBERNETICSCORERESEARCH_PROTOSSAIRWEAPONSLEVEL3))


            #RESEARCH_PSISTORM = 1126
            #RESEARCH_INTERCEPTORGRAVITONCATAPULT = 44


    ######## ARMY PRODUCTION STRUCTURES
    async def army_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random

            # forge for upgrades
            if self.can_afford(FORGE) and not self.units(FORGE).ready.exists and not self.already_pending(FORGE):
                await self.build(FORGE, near=pylon)

            # cannons   front_pylon = self.units(PYLON).ready.closest_to(self.game_info.map_center)
            if self.can_afford(PHOTONCANNON) and self.units(FORGE).ready.exists and self.units(PHOTONCANNON).amount < (self.timemin/2 - 1):
                pylon2 = self.units(PYLON).ready.closest_to(self.game_info.map_center)
                await self.build(PHOTONCANNON, near=pylon2)

            # DARKSHRINE    - DARKTEMPLAR
            if self.units(TWILIGHTCOUNCIL).ready.exists and not self.units(DARKSHRINE):
                if self.can_afford(DARKSHRINE) and not self.already_pending(DARKSHRINE):
                    await self.build(DARKSHRINE, near=pylon)

            #TWILIGHTCOUNCIL  - for blink upgrade
            if self.units(CYBERNETICSCORE).ready.exists and not self.units(TWILIGHTCOUNCIL):
                if self.can_afford(TWILIGHTCOUNCIL) and not self.already_pending(TWILIGHTCOUNCIL):
                    await self.build(TWILIGHTCOUNCIL, near=pylon)

            #robobay for observers
            if self.units(CYBERNETICSCORE).ready.exists and not self.units(ROBOTICSFACILITY):
                if self.can_afford(ROBOTICSFACILITY) and not self.already_pending(ROBOTICSFACILITY):
                    await self.build(ROBOTICSFACILITY, near=pylon)

            #build cybercore
            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)

            #build fleetbeacon
            if self.units(STARGATE).ready.exists and not self.units(FLEETBEACON) and self.timemin > 13:
                if self.can_afford(FLEETBEACON) and not self.already_pending(FLEETBEACON):
                    await self.build(FLEETBEACON, near=pylon)

            #build gateways up to 3
            elif len(self.units(GATEWAY)) < (1 + self.timemin/2) and len(self.units(GATEWAY)) < 3: # 4?
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    await self.build(GATEWAY, near=pylon)

            #stargate for air units
            if self.units(CYBERNETICSCORE).ready.exists:
                if len(self.units(STARGATE)) < (1 + self.timemin/4) and len(self.units(STARGATE)) < 5:
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
                        await self.build(STARGATE, near=pylon)

    ######## TRAINING ARMY UNITS
    async def army_forces(self):
        # mothership
        if self.units(NEXUS).ready.noqueue and self.units(FLEETBEACON).ready and self.can_afford(MOTHERSHIP) and self.supply_left > 0:
                await self.do(self.units(NEXUS).ready.noqueue.random.train(MOTHERSHIP))

        # build carriers only if there are already few tempests
        if self.units(STARGATE).ready.noqueue and self.units(FLEETBEACON).ready and self.can_afford(CARRIER) and self.supply_left > 0:
            if self.units(TEMPEST).amount >= 2:
                await self.do(self.units(STARGATE).ready.noqueue.random.train(CARRIER))

        # build tempests
        if self.units(STARGATE).ready.noqueue and self.units(FLEETBEACON).ready and self.can_afford(TEMPEST) and self.supply_left > 0:
            if self.units(TEMPEST).amount < 4:
                await self.do(self.units(STARGATE).ready.noqueue.random.train(TEMPEST))

        #build phoenix for scout - 5 mins 1 max, from 7 mins 2 max, from 14 mins+ 3 max
        if self.units(STARGATE).ready.noqueue and self.can_afford(PHOENIX) and self.supply_left > 0 and self.units(PHOENIX).amount < (self.timemin/7) and len(self.units(PHOENIX)) < 2:
            await self.do(self.units(STARGATE).ready.noqueue.random.train(PHOENIX))

        #build observer for detection with army - 3 mins 1 max, 5 mins 2 max, 10 mins+ 3 max
        if self.units(ROBOTICSFACILITY).ready.noqueue and self.can_afford(OBSERVER) and self.supply_left > 0 and self.units(OBSERVER).amount < (self.timemin / 5) and self.units(OBSERVER).amount < 3:
            await self.do(self.units(ROBOTICSFACILITY).ready.noqueue.random.train(OBSERVER))

        #build darktemplars
        if self.units(GATEWAY).ready.noqueue and self.units(DARKSHRINE).ready and self.can_afford(DARKTEMPLAR) and self.supply_left > 0:
            if self.units(DARKTEMPLAR).amount < 3:
                await self.do(self.units(GATEWAY).ready.noqueue.random.train(DARKTEMPLAR))

        #build voidrays
        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0 and (self.units(VOIDRAY).amount + self.units(CARRIER).amount) < 10:
                await self.do(sg.train(VOIDRAY))

        #build zealots - up to 9 on 1 min, and up to 1 at 9 min
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.units(ZEALOT).amount < 2 + self.units(STALKER).amount*0.5:
                if self.can_afford(ZEALOT) and self.supply_left > 0:
                    await self.do(gw.train(ZEALOT))

        #build adepts - up to 9 on 1 min, and up to 1 at 9 min
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.units(ADEPT).amount < 2 + self.units(STALKER).amount*0.75 and \
                    self.units(CYBERNETICSCORE).ready.exists:
                if self.can_afford(ADEPT) and self.supply_left > 0:
                    await self.do(gw.train(ADEPT))

        #build stalkers - up to 12 at 4 mins
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.units(STALKER).amount + self.units(VOIDRAY).amount < 12 and self.units(CYBERNETICSCORE).ready:  # 15
                if self.can_afford(STALKER) and self.supply_left > 0:
                    await self.do(gw.train(STALKER))







    ######## MAIN ARMY BEHAVOIUR - GROUND
    async def move_army_ground(self):
        army_units = self.units(STALKER).ready | self.units(ZEALOT).ready | self.units(OBSERVER).ready | \
                     self.units(COLOSSUS).ready | self.units(IMMORTAL).ready | self.units(SENTRY).ready | \
                     self.units(ADEPT).ready
        self.army_count_ground = army_units.amount
        home_location = self.start_location

        if self.army_count_ground < 15:
            # We have less than self.army_size_minimum army in total. Just gather at rally point
            attack_location = self.get_rally_location()
            'if known nearby enemy units exist - attack'
            nearby_enemy_units = self.known_enemy_units.not_structure.closer_than(25, home_location)
            if nearby_enemy_units.not_structure.exists:
                attack_location = self.find_target(self.state)
        else:
            # We have large enough army and have seen an enemy. Attack closest enemy to home
            attack_location = self.find_target(self.state)

        for unit in army_units:
            if unit.shield_percentage + unit.health_percentage > 0.8:
                has_blink = False
                has_guardianshield = False
                if unit.type_id == STALKER:
                    has_blink = await self.has_ability(EFFECT_BLINK_STALKER, unit)  # Do we have blink?
                elif unit.type_id == SENTRY:
                    has_guardianshield = await self.has_ability(GUARDIANSHIELD_GUARDIANSHIELD, unit)

                # Find nearby enemy units
                nearby_enemy_units = self.known_enemy_units.not_structure.closer_than(15, unit)

                # If we don't have any nearby enemies
                if not nearby_enemy_units.not_structure.exists:
                    # If we don't have an attack order, cast one now
                    if not self.has_order(ATTACK, unit) and unit.distance_to(attack_location) > 10:
                        await self.do(unit.attack(attack_location))
                    continue  # Do no further micro

                # Calculate friendly vs enemy army value
                friendly_army_value = self.friendly_army_value(unit, 10)  # 20
                print("ARMY VALUE:  ", str(friendly_army_value))
                if self.supply_used > 180:
                    friendly_army_value *= 1.5
                    print("INCREASED !!!! ARMY VALUE:  ", str(friendly_army_value))
                enemy_army_value = self.enemy_army_value_can_attack_ground(nearby_enemy_units.closest_to(unit), 10)  # 30
                army_advantage = friendly_army_value - enemy_army_value
                # army_advantage = 0

                # If our shield is low, escape a little backwards
                if unit.shield < 10 and unit.type_id not in [ZEALOT]:
                    escape_location = unit.position.towards(home_location, 5)
                    if has_blink:
                        # Stalkers can blink
                        await self.do(unit(EFFECT_BLINK_STALKER, target=escape_location))
                    else:
                        # Others can move normally
                        if not self.has_order(MOVE, unit):
                            await self.do(unit.move(escape_location))

                    continue

                # Do we have an army advantage?
                if army_advantage > 0:
                    # We have a larger army. Engage enemy
                    attack_position = nearby_enemy_units.closest_to(unit).position

                    # If not already attacking, attack
                    if not self.has_order(ATTACK, unit) or not self.has_target(attack_position, unit):
                        await self.do(unit.attack(attack_position))

                    # Activate guardian shield for sentries (if enemy army value is big enough)
                    if has_guardianshield and enemy_army_value > 200:
                        await self.order(unit, GUARDIANSHIELD_GUARDIANSHIELD)
                else:
                    # We have a smaller army, so run back home!
                    if has_blink:
                        # Stalkers can blink
                        await self.order(unit, EFFECT_BLINK_STALKER, home_location)
                    else:
                        # Others can move normally
                        if not self.has_order(MOVE, unit):
                            await self.do(unit.move(home_location))

    ######## MAIN ARMY BEHAVOIUR - AIR
    async def move_army_air(self):
        army_units = self.units(VOIDRAY).ready | self.units(CARRIER).ready | self.units(TEMPEST).ready | self.units(MOTHERSHIP).ready
        self.army_count_air = army_units.amount
        home_location = self.start_location

        if self.army_count_air < 5:
            # We have less than self.army_size_minimum army in total. Just gather at rally point
            attack_location = self.get_rally_location()
            # if there is enemy on our base - attack anyway
            nearby_enemy_units = self.known_enemy_units.not_structure.closer_than(25, home_location)
            if nearby_enemy_units.not_structure.exists:
                attack_location = self.find_target(self.state)
        else:
            # We have large enough army and have seen an enemy. Attack closest enemy to home
            attack_location = self.find_target(self.state)

        for unit in army_units:
            print(str(unit.shield_percentage + unit.health_percentage))
            if (unit.shield_percentage + unit.health_percentage) > 0.8:
                # Find nearby enemy units
                nearby_enemy_units = self.known_enemy_units.not_structure.closer_than(15, unit)

                # If we don't have any nearby enemies
                if not nearby_enemy_units.not_structure.exists:
                    # If we don't have an attack order, cast one now
                    if not self.has_order(ATTACK, unit) and unit.distance_to(attack_location) > 10:
                        await self.do(unit.attack(attack_location))
                    continue  # Do no further micro

                # Calculate friendly vs enemy army value
                friendly_army_value = self.friendly_army_value(unit, 10)  # 20
                print("ARMY VALUE:  ", str(friendly_army_value))
                if self.supply_used > 180:
                    friendly_army_value *= 1.5
                    print("INCREASED !!!! ARMY VALUE:  ", str(friendly_army_value))
                enemy_army_value = self.enemy_army_value_can_attack_air(nearby_enemy_units.closest_to(unit), 10)  # 30
                army_advantage = friendly_army_value - enemy_army_value
                # army_advantage = 0

                # If our shield is low, escape a little backwards
                if unit.shield < 10 and unit.type_id not in [ZEALOT]:
                    escape_location = unit.position.towards(home_location, 5)

                    # Others can move normally
                    if not self.has_order(MOVE, unit):
                        await self.do(unit.move(escape_location))

                    continue

                # Do we have an army advantage?
                if army_advantage > 0:
                    # We have a larger army. Engage enemy
                    attack_position = nearby_enemy_units.closest_to(unit).position

                    # If not already attacking, attack
                    if not self.has_order(ATTACK, unit) or not self.has_target(attack_position, unit):
                        await self.do(unit.attack(attack_position))

                else:
                    # We have a smaller army, so run back home!


                    # Others can move normally
                    if not self.has_order(MOVE, unit):
                        await self.do(unit.move(home_location))



    #pack of scout units moving (flying) over random exp locations and attacking units if can (overlords, for example)
    async def scout(self):
        random_exp_location = random.choice(list(self.expansion_locations.keys()))
        if self.units(PHOENIX).ready.idle.exists:
            for ph in self.units(PHOENIX).ready.idle:
                if ph.shield_percentage < 1:
                    print(str("YO! phoenix is hurt! FALL BACK!"))
                    await self.do(ph.move(self.get_rally_location()))
                # micro for phoenix
                else:
                    await self.do(ph.move(random_exp_location))


    #dark templar wandering between expands, seeking probes to assassinate
    #maybe need some tweeks (sometimes error, + need to optimise exp aggression. firstly visit enemy closest natural)
    async def darktemplars_actions(self):
        random_exp_location = random.choice(list(self.expansion_locations.keys()))
        if self.units(DARKTEMPLAR).ready.exists:
            for ph in self.units(DARKTEMPLAR).ready:
                nearby_enemy_units = self.known_enemy_units.not_structure.closer_than(15, ph)
                if nearby_enemy_units:
                    enemy_workers_around = self.enemy_workers_around(nearby_enemy_units.closest_to(ph), 10)
                    if len(enemy_workers_around) > 0:
                        #print("HEY THERE IS WORKERS NEAR ME!!!!  " + str(len(enemy_workers_around)))
                        #print("HEre they are:  " + str(enemy_workers_around))
                        #get closest enemy worker around to attack
                        attack_target = self.known_enemy_units.filter(lambda unit: unit.type_id in [DRONE, PROBE, SCV]).closest_to(ph)
                        #await self.do(ph.attack(enemy_workers_around[0]))  # targer gets constantly changing... maybe do check if dt has already a target to kill
                        await self.do(ph.attack(attack_target))
            for ph in self.units(DARKTEMPLAR).ready.idle:
                await self.do(ph.move(random_exp_location))


    # for saving LISTED units (when shield depletes, then retreat)
    # after like 5 seconds, at 1 point shield they are commanded again by other script "move_army"
    async def micro_regroup_save(self):
        # blink or just normal micro for staklers
        for s in self.units(STALKER):
            if (s.shield < 1 and s.health_percentage < 0.5) or (s.health_percentage + s.shield_percentage < 0.5):
                if await self.has_ability(EFFECT_BLINK_STALKER, s):  # if have blink, then blink
                    'blink micro here'
                    await self.do(s(EFFECT_BLINK_STALKER, target=home_location))
                else:  # else just try to walk back
                    if not self.has_order(MOVE, s):
                        await self.do(s.move(self.get_rally_location()))
        # normal micro for voidray, carrier
        for s in self.units(VOIDRAY, CARRIER, TEMPEST):
            if (s.shield < 1 and s.health_percentage < 0.5) or (s.health_percentage + s.shield_percentage < 0.5):
                await self.do(s.move(self.get_rally_location()))
        # micro for observer
        for s in self.units(OBSERVER):
            if s.shield_percentage < 1:
                await self.do(s.move(self.get_rally_location()))



    # enable buff if attacking
    async def voidrays_ability(self):
        # enable ability if attacking (better to enable it if attacking heavy armour units)
        for s in self.units(VOIDRAY):
            if s.order_target and s.is_attacking and not s.has_buff(BuffId.VOIDRAYSWARMDAMAGEBOOST) and await self.has_ability(EFFECT_VOIDRAYPRISMATICALIGNMENT, s):  # CANCEL_VOIDRAYPRISMATICALIGNMENT
                #print(str(s.order_target))
                'do ability'
                await self.do(s(EFFECT_VOIDRAYPRISMATICALIGNMENT))

    # intercepters for carrier
    async def carrier_intercepters(self):
        # enable ability if attacking (better to enable it if attacking heavy armour units)
        for s in self.units(CARRIER):
            await self.do(s(BUILD_INTERCEPTORS))






    'TODO!'
    """ GOOD constant stutterstep micro. Maybe for Tempest?
            Usage:
            if unit.weapon_cooldown == 0:
                await self.do(unit.attack(target))
            elif unit.weapon_cooldown < 0:
                await self.do(unit.move(closest_allied_unit_because_cant_attack))
            else:
                await self.do(unit.move(retreatPosition))
            """
    '''
        # helper functions
    
        # this checks if a ground unit can walk on a Point2 position
        def inPathingGrid(self, pos):
            # returns True if it is possible for a ground unit to move to pos - doesnt seem to work on ramps or near edges
            assert isinstance(pos, (Point2, Point3, Unit))
            pos = pos.position.to2.rounded
            return self._game_info.pathing_grid[(pos)] != 0
    '''













    '''
    #this
    run_game(maps.get("AcropolisLE"), [
        Bot(Race.Protoss, BronzeCrawler()),
        Computer(Race.Random, Difficulty.VeryHard)  # CheatInsane VeryHard Hard Medium Easy
        ], realtime=False)
    
    
    #or this
    result = run_game(maps.get("AcropolisLE"), [
        Bot(Race.Protoss, BronzeCrawler()),
        Computer(Race.Random, Difficulty.VeryHard)  # CheatInsane VeryHard Hard Medium Easy
        ], realtime=False)
    print(result)  # Result.Victory     or     Result.Defeat
    '''


def go_play_some_games(amount):
    res = []
    for i in range(amount):
        #result = run_game(maps.get("AcidPlantLE"), [
        result = run_game(maps.random(), [
                Bot(Race.Protoss, BronzeCrawler()),
                Computer(Race.Random, Difficulty.VeryHard)  # CheatInsane VeryHard Hard Medium Easy
                ], realtime=False)
        res.append(print(result))
        print("result from FOR I")
        print(result)
        print("result from FOR I")


    return res







go_play_some_games(1)  # 10

