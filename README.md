# India-Trip-Planner
Knapsack Enhanced India Trip Planner using Greedy Activity Scheduling and Dijkstra's Heuristic

Team Members:

Surabhi Khekale (B3-36)

Aditi Dhamankar (B3-46)

Gauri Joshi (B1-09)

Introduction
This project presents an intelligent trip planning application that helps users generate optimized travel itineraries for Indian tourist destinations.
By combining Knapsack, Activity Selection, and Dijkstra-like heuristic algorithms, the system provides efficient, high-rated travel schedules based on user preferences and available time.
The application is built using Python, featuring a Tkinter GUI and Pandas for data handling.

Objectives
1. Recommend the best tourist spots based on user’s available time and ratings.
2. Optimize the number of locations visited within the given duration.
3. Reduce travel time between destinations using heuristic ordering.
4. Provide an interactive GUI for trip planning, visualization, and itinerary generation.

Algorithms and Techniques Used
1. Knapsack Algorithm
Used to select an optimal subset of tourist spots so that the total visiting time does not exceed the available limit, while maximizing total ratings.
Complexity: O(N × C)
2. Activity Selection Algorithm
Schedules tourist activities efficiently by selecting non-overlapping activities using a greedy approach.
Complexity: O(M log M)
3. Ordering Heuristic (Dijkstra-like)
Applies a nearest-neighbor heuristic to order selected places, minimizing total travel time for each day.
Complexity: O(D × N²)

Tools and Libraries Used
1. Python 3.x
2. Tkinter – for Graphical User Interface
3. Pandas – for data management and manipulation
4. Math / OS modules – for backend logic and system operations
5. CSV Data – dataset of top Indian tourist destinations

How It Works
1. Load the dataset of Indian tourist places.
2. The user selects the available days and preferences.
3. The Knapsack algorithm picks the best spots within time limits.
4. The Activity Selection algorithm schedules non-overlapping visits.
5. The Dijkstra-like heuristic orders them efficiently for travel.
6. The final optimized itinerary is displayed via the Tkinter GUI.

Results
1. Generated itineraries maximize ratings within time limits.
2. Reduced total travel time between destinations.
3. Easy-to-use GUI for smooth user experience.

Future Scope

1. Integration with Google Maps API for real travel distance estimation.
2. Real-time weather and traffic-based adjustments.
3. Multi-city trip planning and hotel suggestions.
4. Mobile app version for on-the-go planning.
5. Machine learning personalization for user preferences.
