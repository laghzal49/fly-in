def run_mini_flyin():
    print("--- Welcome to Mini Fly-In Simulation ---")
    
    # 1. THE GRAPH MAP (Adjacency List)
    # layout: start -> tunnel -> goal
    graph = {
        "start": ["tunnel"],
        "tunnel": ["start", "goal"],
        "goal": ["tunnel"]
    }
    
    # 2. THE PATH FINDER (Hardcoded for this mini exercise)
    # Normally your BFS loop generates this, but let's assume we found it:
    chosen_path = ["start", "tunnel", "goal"]
    
    # 3. DRONE TRACKING
    # We have 2 drones: D1 and D2. Both start at position index 0 ("start")
    # This tracks the INDEX of the zone the drone is currently occupying on chosen_path.
    drone_positions = {
        "D1": 0,  # 0 means chosen_path[0] -> "start"
        "D2": 0   # 0 means chosen_path[0] -> "start"
    }
    
    # Zone capacities (Tunnel can only hold 1 drone at a time!)
    max_drones = {"start": 999, "tunnel": 1, "goal": 999}
    
    # Keep track of how many drones are currently in each zone
    # At turn 0, both drones are sitting at "start"
    zone_occupancy = {"start": 2, "tunnel": 0, "goal": 0}
    
    turn = 0
    
    # The simulation loops until BOTH drones reach the final index (index 2 -> "goal")
    while drone_positions["D1"] < 2 or drone_positions["D2"] < 2:
        turn += 1
        moves_this_turn = []
        
        # We check each drone one by one every turn
        for drone_id in ["D1", "D2"]:
            current_index = drone_positions[drone_id]
            
            # If the drone is already at the goal, it doesn't move anymore
            if current_index == 2:
                continue
                
            current_zone = chosen_path[current_index]
            next_zone = chosen_path[current_index + 1]
            
            # RULE CHECK: Can we enter the next zone?
            if zone_occupancy[next_zone] < max_drones[next_zone]:
                # 1. Vacate current zone capacity
                zone_occupancy[current_zone] -= 1
                
                # 2. Occupy next zone capacity
                zone_occupancy[next_zone] += 1
                
                # 3. Update drone position index
                drone_positions[drone_id] = current_index + 1
                
                # Record the move using the mandatory project format: D<ID>-<zone>
                moves_this_turn.append(f"{drone_id}-{next_zone}")
            else:
                # If next zone is full, this drone does nothing this turn (It Waits!)
                pass
                
        # Print the output for this specific turn if anyone moved
        if moves_this_turn:
            print(f"Turn {turn}: " + " ".join(moves_this_turn))

# Run our mini assignment engine!
run_mini_flyin()
