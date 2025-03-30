import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lattice_clock import LatticeClockSystem, demo_callback
from sunset_time_calc import SunsetCalculator

if __name__ == "__main__":
    # Create the lattice clock
    lattice = LatticeClockSystem()

    # Import needed modules for the demo
    # In production, these would be properly imported at the top
    import sys

    sys.path.append("./")  # Ensure our other modules can be found
    # Create sunset calculator and generate grid for demo regions
    calculator = SunsetCalculator()

    # For demo purposes, create small grids for a few regions
    sf_grid = calculator.get_grid_sunset_times(
        37.0, -123.0, 38.0, -121.0, grid_size=0.5
    )
    ny_grid = calculator.get_grid_sunset_times(40.0, -75.0, 41.0, -73.0, grid_size=0.5)

    # Add grids to the lattice clock
    lattice.add_sunset_grid("SF_Bay_Area", sf_grid)
    lattice.add_sunset_grid("NY_Area", ny_grid)

    # For flight data demo, we would also import:
    # from flight_data_parser import FlightDataFetcher
    # fetcher = FlightDataFetcher()

    # Register a simple callback for demo
    lattice.register_callback(demo_callback)

    # Register a more complex callback for handling flight data
    # Using a lambda to pass additional arguments
    # lattice.register_callback(
    #     lambda timestamp: flight_data_callback(timestamp, fetcher, calculator, lattice)
    # )

    # Start the clock
    print("Starting Lattice Clock demonstration...")
    lattice.start()

    # Run for a short demo period
    try:
        time.sleep(10)  # Run for 10 seconds
    except KeyboardInterrupt:
        print("Demo interrupted")

    # Stop the clock
    lattice.stop()
    print("Lattice Clock demonstration completed")
