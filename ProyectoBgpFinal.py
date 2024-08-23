# importaciones
import requests
from datetime import datetime
import customtkinter as ctk
from tkcalendar import Calendar
import tkinter as tk
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from ipywidgets import interact, IntSlider, VBox
from adjustText import adjust_text
import keyboard


# Función para convertir una fecha y hora a formato Unix
def convert_to_unix(year, month, day, hour, minute, second):
    dt = datetime(year, month, day, hour, minute, second)
    return int(dt.timestamp())

# Función para manejar la solicitud de la API y mostrar los datos en una nueva ventana
def fetch_data():
    global data
    ip_address = ip_entry.get()
    start_date = start_date_var.get()
    end_date = end_date_var.get()
    #ASN_number = ASN_entry.get()

    start_datetime = datetime.strptime(start_date + ' ' + start_hour_entry.get() + ':' + start_minute_entry.get() + ':' + start_second_entry.get(), '%Y-%m-%d %H:%M:%S')
    end_datetime = datetime.strptime(end_date + ' ' + end_hour_entry.get() + ':' + end_minute_entry.get() + ':' + end_second_entry.get(), '%Y-%m-%d %H:%M:%S')

    start_time = convert_to_unix(start_datetime.year, start_datetime.month, start_datetime.day, start_datetime.hour, start_datetime.minute, start_datetime.second)
    end_time = convert_to_unix(end_datetime.year, end_datetime.month, end_datetime.day, end_datetime.hour, end_datetime.minute, end_datetime.second)
    
    start_time = start_time - 21600
    end_time = end_time - 21600

    print("start", start_time, "end: ", end_time)
    url = f"https://stat.ripe.net/data/bgplay/data.json?endtime={end_time}&resource={ip_address}&rrcs=0%2C1%2C5%2C6%2C7%2C10%2C11%2C13%2C14%2C15%2C16%2C18%2C20&starttime={start_time}&unix_timestamps=TRUE"
    response = requests.get(url)
    print(url)
    if response.status_code == 200:
        data = response.json()
        process_node(data)
        #process_data(data)
    else:
        output_label.configure(text=f"Error: No se pudo obtener datos. Código de estado: {response.status_code}")
        
    return data

# Función para obtener nodos
def process_node(data):
    nodes = set()
    edges = []
    destination_node = set()

    for event in data['data']['events']:
        if event['type'] == 'A':  # Tipo A para anuncios
            if 'target_prefix' in event['attrs'] and 'path' in event['attrs']:
                prefix = event['attrs']['target_prefix']
                path = event['attrs']['path']
                destination_node.add(path[0])

                for i in range(len(path) - 1):
                    nodes.add(path[i])
                    nodes.add(path[i + 1])
                    edges.append((path[i], path[i + 1]))
            else:
                print(f"Evento sin 'target_prefix' o 'path': {event}")
    #print(data['data']['events'])
    #print(nodes)
    update_nodes(destination_node)

# Función para procesar los datos de la API y actualizar el diagrama
def process_data():
    global data
    global filtered_events
    global current_index
    current_index = 0
    filtered_events = []
    destination_asn = int(destination_var.get())
    check_nextw = 0
    for event in data['data']['events']:
        if event['type'] in ['A', 'W']:
            if 'path' in event['attrs']:
                asn_path = event['attrs']['path']
                if asn_path[0] == destination_asn:
                    filtered_events.append({
                        'timestamp': event['timestamp'],
                        'asn_path': asn_path,
                        'event_type': event['type']
                    })
                    #levantar bandera para siguiente instruccion
                    check_nextw = 1
                
                
            elif event['type'] == 'W':
                if(check_nextw == 1):
                    filtered_events.append({
                        'timestamp': event['timestamp'],
                        'asn_path': [],
                        'event_type': event['type']
                    })
                    check_nextw = 0
    print(filtered_events)
    # Trigger the slideshow once the data is processed
    if filtered_events:
        plot_as_path(current_index)


#funcion para detectar teclado
def next_figure(event=None):  
    """Go to the next figure."""  
    global current_index  
    global filtered_events
    print("d pressed")
    current_index = (current_index + 1) % len(filtered_events)  # Go to next figure  
    plot_as_path(current_index)  

def previous_figure(event=None):  
    """Go to the previous figure."""  
    global current_index  
    current_index = (current_index - 1) % len(filtered_events)  # Go to previous figure  
    plot_as_path(current_index)  


def plot_as_path(index):  
    # Ensure there are at least three events to plot  
    if index < 0 or index + 2 >= len(filtered_events):  
        raise ValueError("Not enough events to plot three subplots.")  
    
    # Create a figure for the subplots  
    fig, axes = plt.subplots(3, 1, figsize=(10, 18))  # 3 rows, 1 column  

    for i in range(3):  
        event = filtered_events[index + i]  
        G = nx.DiGraph()  

        # Handle "W" event  
        if event['event_type'] == 'W' or not event['asn_path']:  
            G.add_node('Origin')  
        else:  
            path = event['asn_path'] + ['Origin']  # Add 'Origin' at the end  
            edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]  
            G.add_edges_from(edges)  

        # Draw the graph in the corresponding subplot  
        pos = nx.circular_layout(G)  
        nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=2000, font_size=15, font_weight="bold", edge_color='gray', ax=axes[i])  
        axes[i].set_title(f"Timestamp: {event['timestamp']} | Event Type: {event['event_type']}")  

    plt.tight_layout()  # Adjust layout to prevent overlap  
    plt.show() 
# Función para actualizar el dropdown con los nodos de destino
def update_nodes(destination_node):
    global destination_nodes, destination_nodes_list
    # Update the set with new values
    destination_nodes = destination_node
    destination_nodes_list = list(destination_nodes)  # Convert the updated set to a list
    destination_nodes_list = list(map(str, destination_nodes))
    # Update the CTkOptionMenu with the new values
    destination_dropdown.configure(values=destination_nodes_list)
    destination_var.set(destination_nodes_list[0])  # Reset to the first option
    
# Función para extaer los datos para el BGP State
def get_bgp_state():
    ip_address_state = ip_entry_State.get()
    date_state = date_var_state.get()

    datetime_state = datetime.strptime(date_state + ' ' + hour_entry_st.get() + ':' + minute_entry_st.get() + ':' + second_entry_st.get(), '%Y-%m-%d %H:%M:%S')
    
    time_state = convert_to_unix(datetime_state.year, datetime_state.month, datetime_state.day, datetime_state.hour, datetime_state.minute, datetime_state.second)
    
    time_state = time_state - 21600

    print("time", time_state)
    url = f"https://stat.ripe.net/data/bgp-state/data.json?resource={ip_address_state}&timestamp={time_state}"
    response = requests.get(url)
    print(url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        process_bgp_state_data(data)
    else:
        output_label.configure(text=f"Error: No se pudo obtener datos. Código de estado: {response.status_code}")

# Función para procesar los datos del BGP State y mostrar el diagrama
def process_bgp_state_data(data):
    # Verificar si la clave 'data' existe en la respuesta
    if 'data' in data:
        bgp_state = data['data'].get('bgp_state', [])
        
        # Verificar si hay datos en 'bgp_state'
        if not bgp_state:
            print("No hay datos de estado BGP disponibles.")
            return
        
        for state in bgp_state:
            target_prefix = state.get('target_prefix', 'Desconocido')
            source_id = state.get('source_id', 'Desconocido')
            path = state.get('path', [])
            community = state.get('community', [])
            
            # Imprimir o procesar los datos según sea necesario
            print(f"Target Prefix: {target_prefix}")
            print(f"Source ID: {source_id}")
            print(f"Path: {path}")
            print(f"Community: {community}")
            
        # Crear el diagrama de propagación
        plot_bgp_state_diagram(bgp_state)
            
    else:
        print("No se encontró la clave 'data' en la respuesta.")

# Función para crear el diagrama de propagación de BGP State        
def plot_bgp_state_diagram(bgp_state):
    G = nx.DiGraph()
    
    # Añadir nodos y arcos al grafo
    for state in bgp_state:
        target_prefix = state.get('target_prefix', 'Desconocido')
        path = state.get('path', [])
        
        # Añadir nodos para el path
        for i in range(len(path)):
            G.add_node(path[i])
            if i > 0:
                # Añadir arcos entre nodos
                G.add_edge(path[i-1], path[i])
    
    # Ajustar el parámetro k para una mayor dispersión de nodos
    pos = nx.spring_layout(G, k=2000, iterations = 10, scale = 4)  # Aumenta o disminuye k para ajustar la dispersión
    
    plt.figure(figsize=(50, 50))
    
    # Dibujar los nodos y arcos
    nx.draw(G, pos, with_labels=False, node_size=1000, node_color='lightblue', font_size=10, font_weight='bold', arrows=True)
    
    # Ajustar las etiquetas
    labels = {n: str(n) for n in G.nodes()}
    texts = [plt.text(pos[n][0], pos[n][1], labels[n], ha='center', va='center') for n in G.nodes()]
    adjust_text(texts, arrowprops=dict(arrowstyle="->", color='red'))
    
    plt.title('Diagrama de Propagación de Rutas BGP')
    plt.show()

# Función para crear el diagrama de propagación con nodos movibles
def create_diagram(nodes, edges):
    G = nx.DiGraph()

    for node in nodes:
        G.add_node(node)

    for edge in edges:
        G.add_edge(*edge)

    pos = nx.spring_layout(G, k=1, seed=42)

    fig, ax = plt.subplots(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_weight='bold', ax=ax)

    def on_press(event):
        if event.inaxes == ax:
            for node, (x, y) in pos.items():
                if np.sqrt((event.xdata - x)**2 + (event.y)**2) < 0.05:
                    selected_node[0] = node

    def on_drag(event):
        if selected_node[0] is not None:
            x, y = event.xdata, event.ydata
            pos[selected_node[0]] = (x, y)
            ax.clear()
            nx.draw(G, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_weight='bold', ax=ax)
            plt.draw()

    def on_release(event):
        selected_node[0] = None

    selected_node = [None]
    fig.canvas.mpl_connect('button_press_event', on_press)
    fig.canvas.mpl_connect('motion_notify_event', on_drag)
    fig.canvas.mpl_connect('button_release_event', on_release)

    plt.title("Diagrama de Propagación de Prefijos")
    plt.show()

# Configuración de la interfaz gráfica
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Propagación de Prefijos en Internet")

# Creación del Tabview
tab_view = ctk.CTkTabview(root)
tab_view.pack(expand=True, fill="both")

#----------------------------------------------------------------------------------------------
# BGP Play (Pestaña principal)
#----------------------------------------------------------------------------------------------

main_tab = tab_view.add("BGP Play")
frame = ctk.CTkFrame(master=main_tab)
frame.pack(pady=20, padx=60, fill="both", expand=True)

title_label = ctk.CTkLabel(master=frame, text="Propagación de Prefijos en Internet", font=("Roboto", 24))
title_label.pack(pady=12, padx=10)

# Campos de entrada para la dirección IP
ip_label = ctk.CTkLabel(master=frame, text="Dirección IP:")
ip_label.pack(pady=5, padx=10)

ip_entry = ctk.CTkEntry(master=frame, placeholder_text="Ingrese la dirección IP")
ip_entry.pack(pady=5, padx=10)

# Fecha y hora de inicio
start_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
formato_fecha_label = ctk.CTkLabel(master=frame, text="Formato de fecha: YYYY-MM-DD")
formato_fecha_label.pack(pady=2, padx=10)

start_date_label = ctk.CTkLabel(master=frame, text="Fecha de inicio:")
start_date_label.pack(pady=5, padx=10)

start_date_entry = ctk.CTkEntry(master=frame, textvariable=start_date_var, width=150, justify="center")
start_date_entry.pack(pady=5, padx=10)

# Campos de hora, minuto y segundo de inicio
start_time_frame = ctk.CTkFrame(master=frame)
start_time_frame.pack(pady=5, padx=10)

start_hour_entry = ctk.CTkEntry(master=start_time_frame, placeholder_text="Hora", width=80)
start_hour_entry.insert(0, "00")
start_hour_entry.grid(row=0, column=0, padx=5)

start_minute_entry = ctk.CTkEntry(master=start_time_frame, placeholder_text="Minuto", width=80)
start_minute_entry.insert(0, "00")
start_minute_entry.grid(row=0, column=1, padx=5)

start_second_entry = ctk.CTkEntry(master=start_time_frame, placeholder_text="Segundo", width=80)
start_second_entry.insert(0, "00")
start_second_entry.grid(row=0, column=2, padx=5)

# Fecha y hora de fin
end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
end_date_label = ctk.CTkLabel(master=frame, text="Fecha de fin:")
end_date_label.pack(pady=5, padx=10)

end_date_entry = ctk.CTkEntry(master=frame, textvariable=end_date_var, width=150, justify="center")
end_date_entry.pack(pady=5, padx=10)

# Campos de hora, minuto y segundo de fin
now = datetime.now()
end_time_frame = ctk.CTkFrame(master=frame)
end_time_frame.pack(pady=5, padx=10)
end_hour_entry = ctk.CTkEntry(master=end_time_frame, placeholder_text="Hora", width=80)
end_hour_entry.insert(0, now.strftime('%H'))
end_hour_entry.grid(row=0, column=0, padx=5)

end_minute_entry = ctk.CTkEntry(master=end_time_frame, placeholder_text="Minuto", width=80)
end_minute_entry.insert(0, now.strftime('%M'))
end_minute_entry.grid(row=0, column=1, padx=5)

end_second_entry = ctk.CTkEntry(master=end_time_frame, placeholder_text="Segundo", width=80)
end_second_entry.insert(0, now.strftime('%S'))
end_second_entry.grid(row=0, column=2, padx=5)

# Campos de entrada para la dirección IP
ASN_label = ctk.CTkLabel(master=frame, text="ASN destino:")
ASN_label.pack(pady=5, padx=10)

#ASN_entry = ctk.CTkEntry(master=frame, placeholder_text="Ingrese el ASN destino")
#ASN_entry.pack(pady=5, padx=10)

# Dropdown para nodos de destino
#destination_var = tk.StringVar()
#destination_dropdown = tk.OptionMenu(root, destination_var, "Selecciona un nodo de destino")
#destination_dropdown.pack(pady=15, padx=10)

# Initial set of destination nodes
destination_nodes = {"Selecciona un nodo de destino", "Nodo 1", "Nodo 2", "Nodo 3"}

# Convert the set to a list for the OptionMenu
destination_nodes_list = list(destination_nodes)

destination_var = ctk.StringVar(value=destination_nodes_list[0])
destination_dropdown = ctk.CTkOptionMenu(master = frame, variable=destination_var, values=destination_nodes_list)
destination_dropdown.pack(pady=5, padx=10)

# Botón para obtener datos y actualizar la interfaz
obtener_datos_button = ctk.CTkButton(master=frame, text="Obtener Datos", command=fetch_data)
obtener_datos_button.pack(pady=15, padx=10)

# Botón para aplicar y actualizar el diagrama
aplicar_button = ctk.CTkButton(master=frame, text="Aplicar", command=lambda: process_data())
aplicar_button.pack(pady=15, padx=10)

# Etiqueta para mostrar la salida o mensajes de error
output_label = ctk.CTkLabel(master=frame, text="")
output_label.pack(pady=5, padx=10)

#----------------------------------------------------------------------------------------------
# BGP State
#----------------------------------------------------------------------------------------------

BGP_state = tab_view.add("BGP State")
frame2 = ctk.CTkFrame(master=BGP_state)
frame2.pack(pady=20, padx=60, fill="both", expand=True)

title_label2 = ctk.CTkLabel(master=frame2, text="Propagación de Prefijos en Internet", font=("Roboto", 24))
title_label2.pack(pady=12, padx=10)

# Campos de entrada para la dirección IP
ip_label_State = ctk.CTkLabel(master=frame2, text="Dirección IP:")
ip_label_State.pack(pady=5, padx=10)

ip_entry_State = ctk.CTkEntry(master=frame2, placeholder_text="Ingrese la dirección IP")
ip_entry_State.pack(pady=5, padx=10)

# Fecha y hora actual
date_var_state = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
formato_fecha_label_state = ctk.CTkLabel(master=frame2, text="Formato de fecha: YYYY-MM-DD")
formato_fecha_label_state.pack(pady=2, padx=10)

date_label_st = ctk.CTkLabel(master=frame2, text="Fecha de inicio:")
date_label_st.pack(pady=5, padx=10)

date_entry_st = ctk.CTkEntry(master=frame2, textvariable=date_var_state, width=150, justify="center")
date_entry_st.pack(pady=5, padx=10)

# Campos de hora, minuto y segundo de inicio
time_frame_st = ctk.CTkFrame(master=frame2)
time_frame_st.pack(pady=5, padx=10)

hour_entry_st = ctk.CTkEntry(master=time_frame_st, placeholder_text="Hora", width=80)
hour_entry_st.insert(0, "00")
hour_entry_st.grid(row=0, column=0, padx=5)

minute_entry_st = ctk.CTkEntry(master=time_frame_st, placeholder_text="Minuto", width=80)
minute_entry_st.insert(0, "00")
minute_entry_st.grid(row=0, column=1, padx=5)

second_entry_st = ctk.CTkEntry(master=time_frame_st, placeholder_text="Segundo", width=80)
second_entry_st.insert(0, "00")
second_entry_st.grid(row=0, column=2, padx=5)

# Botón para obtener el estado BGP
get_state_button = ctk.CTkButton(master=frame2, text="Mostrar Diagrama", command=get_bgp_state)
get_state_button.pack(pady=15, padx=10)

# Bind keys to next and previous figure functions  
root.bind("<a>", previous_figure)  # Press 'a' to go to the previous figure  
root.bind("<d>", next_figure)       # Press 'd' to go to the next figure  

root.mainloop()
