import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import math
import os

# --- Global Configuration and Constants ---

CSV_FILE = "Top Indian Places to Visit.csv"
DF = None

SLOT_START = {
    'Morning': 8, 'Afternoon': 13, 'Evening': 17, 'Night': 21, 
    'All': 10, 'Anytime': 10, 'None': 10 
}
AVG_SPEED_KMH = 50.0  
WORKING_HOURS_PER_DAY = 10 

# --- 1. Data Loader and Cleaner ---

def load_data():
    """Loads the CSV data and cleans relevant columns."""
    global DF
    if not os.path.exists(CSV_FILE):
        messagebox.showerror("File Error", f"The required file '{CSV_FILE}' was not found in the current directory.")
        return None
    
    try:
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip()
        
        df.rename(columns={
            'State': 'State', 'City': 'City', 'Name': 'Place_Name',
            'time needed to visit in hrs': 'Time_Needed', 'Google review rating': 'Rating',
            'Best Time to visit': 'Best_Time'
        }, inplace=True)
        
        df['Time_Needed'] = pd.to_numeric(df['Time_Needed'], errors='coerce').fillna(1.0)
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(3.5)
        df.dropna(subset=['State', 'City', 'Place_Name'], inplace=True)
        
        DF = df
        return df
    except Exception as e:
        messagebox.showerror("Data Error", f"Failed to load or process CSV file: {e}")
        return None

def get_states():
    """Returns a sorted list of unique states."""
    if DF is not None:
        return sorted(DF['State'].unique())
    return []

def get_cities_for_state(state):
    """Returns a sorted list of unique cities for a given state."""
    if DF is not None and state:
        return sorted(DF[DF['State'] == state]['City'].unique())
    return []

def get_places_for_city(state, city):
    """Returns a list of place objects for a given city, sorted by rating."""
    if DF is None or not state or not city:
        return []
    
    places_df = DF[(DF['State'] == state) & (DF['City'] == city)].copy()
    places_df.sort_values(by='Rating', ascending=False, inplace=True)
    
    
    places_list = []
    for idx, row in places_df.iterrows():
        places_list.append({
            'index': idx, 
            'name': row['Place_Name'],
            'time_needed': row['Time_Needed'],
            'rating': row['Rating'],
            'best_time': row['Best_Time']
        })
    return places_list


# --- 2. Optimization Algorithms ---

def knapsack_optimizer(places, total_time_capacity):
    """
    STAGE 1: Solves the 0/1 Knapsack problem (Dynamic Programming).
    Maximizes total rating (value) without exceeding total time (weight/capacity).
    """
    if not places or total_time_capacity <= 0:
        return []


    PRECISION_FACTOR = 100 
    capacity = int(total_time_capacity * PRECISION_FACTOR)
    
    items = []
    for p in places:
        value = int(p.get('rating', 3.5) * PRECISION_FACTOR) 
        weight = int(p.get('time_needed', 1.0) * PRECISION_FACTOR)
        
        if weight > 0 and value > 0 and weight <= capacity:
            items.append({'place': p, 'value': value, 'weight': weight})

    if not items:
        return []

    n = len(items)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        item = items[i - 1]
        for w in range(capacity + 1):
            if item['weight'] <= w:
                dp[i][w] = max(dp[i - 1][w], item['value'] + dp[i - 1][w - item['weight']])
            else:
                dp[i][w] = dp[i - 1][w]

    selected_places = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected_places.append(items[i - 1]['place'])
            w -= items[i - 1]['weight'] 

    return selected_places

def create_activities(places, num_days):
    """Generates candidate time intervals for places across the trip days."""
    candidates = []
    for day in range(1, num_days + 1):
        day_offset = (day - 1) * 24
        for p in places:
            best_time_str = str(p.get('best_time', 'All')).split(' ')[0] 
            slot_base = SLOT_START.get(best_time_str, SLOT_START['All'])
            
            start = day_offset + slot_base
            end = start + p.get('time_needed', 1.0)
            if (end % 24) < 23:
                candidates.append({
                    'start': start, 'end': end, 'place': p, 'day': day
                })
    return candidates

def activity_selection_greedy(candidates):
    """
    STAGE 2: Activity Selection Algorithm.
    Greedily selects the maximum number of non-overlapping activities (places) by earliest finish time.
    """
    if not candidates:
        return []
        
    candidates_sorted = sorted(candidates, key=lambda x: x['end'])
    selected = []
    last_finish = -1 
    chosen_place_names = set() 
    
    for c in candidates_sorted:
        if c['start'] >= last_finish and c['place']['name'] not in chosen_place_names:
            selected.append(c)
            last_finish = c['end']
            chosen_place_names.add(c['place']['name'])
            
    return selected

def travel_time_between(p1, p2):
    """
    Simple distance model: Dijkstra's cost metric (travel time in hours).
    Assumes intra-city travel is short, inter-city is longer.
    """
    city1 = p1['city']
    city2 = p2['city']
    
    if city1 == city2:
        return 0.5  
    else:
        return 3.0  

def order_selected_places(selected_activities):
    """
    STAGE 3: Dijkstra's-like Greedy Nearest-Neighbor Heuristic for path ordering.
    Orders the scheduled places first by day, then for minimum travel time within each day.
    """
    if not selected_activities:
        return [], 0.0

    daily_activities = {}
    for activity in selected_activities:
        day = activity['day']
        if day not in daily_activities:
            daily_activities[day] = []
        daily_activities[day].append(activity)

    for day in daily_activities:
        daily_activities[day].sort(key=lambda x: x['start'])

    ordered_route = []
    total_travel_time = 0.0

    sorted_days = sorted(daily_activities.keys())

    for day in sorted_days:
        remaining_in_day = daily_activities[day]
        
        current_day_route = [remaining_in_day.pop(0)] 
        
        while remaining_in_day:
            current_place_node = current_day_route[-1]
            current_place = current_place_node['place']
            
            best_idx = -1
            best_travel_time = float('inf')

            for idx, cand_node in enumerate(remaining_in_day):
                cand_place = cand_node['place']
                
                t = travel_time_between(current_place, cand_place)
                
                if t < best_travel_time:
                    best_travel_time = t
                    best_idx = idx
                elif t == best_travel_time and cand_place['rating'] > remaining_in_day[best_idx]['place']['rating']:
                    best_travel_time = t
                    best_idx = idx

            if best_idx != -1:
                total_travel_time += best_travel_time
                current_day_route.append(remaining_in_day.pop(best_idx))
            else:
                break
        if ordered_route:
             pass 
        
        ordered_route.extend(current_day_route)
        
    return ordered_route, total_travel_time


# --- 3. Tkinter GUI Application ---

class JourneyPlannerApp:
    def __init__(self, master):
        self.master = master
        master.title("India Trip Planner (Python GUI) - Knapsack Enhanced")
        master.geometry("600x750")

        self.places_data = []
        self.selected_city = tk.StringVar(master)
        self.selected_state = tk.StringVar(master)
        
        if load_data() is None:
            master.destroy()
            return
            
        self.create_widgets()

    def create_widgets(self):
        
        input_frame = ttk.LabelFrame(self.master, text="Client & Trip Details", padding="10")
        input_frame.pack(padx=10, pady=10, fill="x")

        def create_input_field(parent, row, label_text, var_name, default_value=""):
            ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            entry = ttk.Entry(parent, width=30)
            entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
            entry.insert(0, default_value)
            setattr(self, var_name, entry)
            return entry

        create_input_field(input_frame, 0, "Name:", "name_entry", "Traveler")
        create_input_field(input_frame, 1, "Email ID:", "email_entry", "example@mail.com")
        create_input_field(input_frame, 2, "Phone Number:", "phone_entry", "9876543210")
        create_input_field(input_frame, 3, "No. of People:", "people_entry", "1")

        create_input_field(input_frame, 4, "No. of Days:", "days_entry", "3")
        create_input_field(input_frame, 5, "No. of Nights:", "nights_entry", "2")
        
        loc_frame = ttk.LabelFrame(self.master, text="Location Selection", padding="10")
        loc_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(loc_frame, text="Select State:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.state_combo = ttk.Combobox(loc_frame, textvariable=self.selected_state, values=get_states(), state="readonly", width=27)
        self.state_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.state_combo.bind("<<ComboboxSelected>>", self.update_cities)
        
        ttk.Label(loc_frame, text="Select City:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.city_combo = ttk.Combobox(loc_frame, textvariable=self.selected_city, values=[], state="readonly", width=27)
        self.city_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.city_combo.bind("<<ComboboxSelected>>", self.update_places)
        
        places_frame = ttk.LabelFrame(self.master, text="Select Tourist Places (Knapsack will filter for Max Rating)", padding="10") # Updated label
        places_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.places_listbox = tk.Listbox(places_frame, selectmode=tk.MULTIPLE, height=12)
        self.places_listbox.pack(fill="both", expand=True)
        
        ttk.Button(self.master, text="Generate Optimized Journey", command=self.plan_journey).pack(pady=15, padx=10, fill="x")

    def update_cities(self, event=None):
        """Updates the City Combobox based on the selected State."""
        state = self.state_combo.get()
        cities = get_cities_for_state(state)
        
        self.city_combo['values'] = cities
        self.city_combo.set('')
        self.places_listbox.delete(0, tk.END)
        self.places_data = []

    def update_places(self, event=None):
        """Updates the Places Listbox based on the selected City."""
        state = self.state_combo.get()
        city = self.city_combo.get()
        
        self.places_listbox.delete(0, tk.END)
        self.places_data = get_places_for_city(state, city)
        
        if not self.places_data:
            self.places_listbox.insert(tk.END, "No places found for this city.")
            return

        for place in self.places_data:
            display_text = f"{place['name']} ({place['rating']}★ | {place['time_needed']}hrs | Best: {place['best_time']})"
            self.places_listbox.insert(tk.END, display_text)

    # --- Journey Planning and Display ---
    
    def plan_journey(self):
        """
        Executes the 3-Stage Optimization: Knapsack -> Activity Selection -> Ordering.
        """
        
        try:
            client_info = {
                'name': self.name_entry.get(), 'email': self.email_entry.get(),
                'phone': self.phone_entry.get(), 'people': int(self.people_entry.get() or 1),
                'days': int(self.days_entry.get() or 1), 'nights': int(self.nights_entry.get() or 0),
                'state': self.state_combo.get(), 'city': self.city_combo.get(),
            }
            if client_info['days'] < 1 or not client_info['state'] or not client_info['city']:
                raise ValueError("Please fill in all mandatory fields (Days, State, City).")
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return
        
        selected_indices = self.places_listbox.curselection()
        
        if not selected_indices:
             messagebox.showinfo("Selection Required", "Please select at least one tourist place from the list.")
             return

        candidate_pool = [self.places_data[i] for i in selected_indices]
        for p in candidate_pool:
            p['city'] = client_info['city']
            
        total_time_capacity = client_info['days'] * WORKING_HOURS_PER_DAY
        
        optimal_places = knapsack_optimizer(candidate_pool, total_time_capacity)
        
        if not optimal_places:
             messagebox.showinfo("No Knapsack Solution", 
                                 f"The Knapsack algorithm found no combination of your selected places that fits within your {client_info['days']} days ({total_time_capacity} hours total capacity). Try selecting shorter activities.")
             return
        
        all_candidate_activities = create_activities(optimal_places, client_info['days'])
        selected_activities = activity_selection_greedy(all_candidate_activities)
        
        if not selected_activities:
            messagebox.showinfo("No Itinerary", "The scheduler could not fit the Knapsack-selected places into non-overlapping time slots.")
            return

        ordered_route_activities, total_travel_time_only = order_selected_places(selected_activities)

        self.display_itinerary(client_info, ordered_route_activities, total_travel_time_only)

    def display_itinerary(self, client_info, route_activities, total_travel_time_only):
        """Creates a new window to display the finalized journey."""
        result_window = tk.Toplevel(self.master)
        result_window.title("Optimized Journey Itinerary (Knapsack Enhanced)")
        result_window.geometry("900x650")

        info_frame = ttk.LabelFrame(result_window, text="Client & Trip Summary", padding="10")
        info_frame.pack(padx=10, pady=10, fill="x")
        
        total_distance = round(total_travel_time_only * AVG_SPEED_KMH, 2)
        total_activity_time = sum(node['place']['time_needed'] for node in route_activities)

        summary_text = f"""
Name: {client_info['name']} | Email: {client_info['email']} | Phone: {client_info['phone']}
People: {client_info['people']} | Days: {client_info['days']} | Nights: {client_info['nights']}
Location: {client_info['city']}, {client_info['state']}
Total Activity Time Scheduled: {round(total_activity_time, 2)} hrs (Knapsack Max Value)
Total Estimated Travel Time (in route): {round(total_travel_time_only, 2)} hrs
Total Estimated Travel Distance (at {AVG_SPEED_KMH} km/h): {total_distance} km
"""
        tk.Label(info_frame, text=summary_text, justify=tk.LEFT, padx=10, font=('Arial', 10, 'bold')).pack(fill="x")
        
        tk.Label(info_frame, text=f"**Note:** Knapsack filter was applied. Only the {len(route_activities)} highest-rated, time-efficient activities were selected from your choices to fit the total time capacity.", 
                 justify=tk.LEFT, fg='blue').pack(fill="x") 

        table_frame = ttk.LabelFrame(result_window, text="Optimized Itinerary", padding="10")
        table_frame.pack(padx=10, pady=10, fill="both", expand=True)

        columns = ("Order", "Day", "Place", "Time Slot (24hr)", "Rating", "Time Needed (hrs)", "Travel Time to Next (hrs)", "Distance to Next (km)")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
        
        tree.column("Place", width=180, anchor='w')
        tree.column("Time Slot (24hr)", width=120, anchor='w')
        tree.column("Day", width=50)

        # Populate the table
        for i, node in enumerate(route_activities):
            p = node['place']
            
            travel_duration_hrs = 0.0
            travel_distance_km = 0.0
            
            if i < len(route_activities) - 1:
                next_place = route_activities[i+1]['place']
                travel_duration_hrs = travel_time_between(p, next_place) 
                travel_distance_km = travel_duration_hrs * AVG_SPEED_KMH 
            
            start_hour = int(node['start'] % 24)
            end_hour = int(node['end'] % 24)
            time_slot_str = f"{start_hour:02d}:00 - {end_hour:02d}:00"

            tree.insert("", tk.END, values=(
                i + 1,
                node['day'], 
                p['name'],
                time_slot_str,
                f"{p['rating']} ★",
                round(p['time_needed'], 1),
                round(travel_duration_hrs, 2),
                round(travel_distance_km, 2)
            ))

        tree.pack(fill="both", expand=True)


if __name__ == '__main__':
    root = tk.Tk()
    app = JourneyPlannerApp(root)
    if DF is not None:
        root.mainloop()