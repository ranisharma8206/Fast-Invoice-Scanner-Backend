class Active_connections:
    connection_pair_list = []
    def add_connection(self, username, viewer_ws_id):
        new_connection = Connection(username, viewer_ws_id)
        Active_connections.connection_pair_list.append(new_connection)
    
    def remove_connection(self, connection_pair_id):
        for c in Active_connections.connection_pair_list:
            if c.connection_pair_id == connection_pair_id : 
                Active_connections.connection_pair_list.remove(c)

    def access_objects(self, connection_pair_id = None, username = None, viewer_ws_id = None, scanner_ws_id = None):
        if connection_pair_id != None:
            for c in Active_connections.connection_pair_list:
                if c.connection_pair_id == connection_pair_id:
                    return c
        elif username != None:
            for c in Active_connections.connection_pair_list:
                if c.username == username:
                    return c
        elif viewer_ws_id != None:
            for c in Active_connections.connection_pair_list:
                if c.viewer_ws_id == viewer_ws_id:
                    return c
        elif scanner_ws_id != None:
            for c in Active_connections.connection_pair_list:
                if c.scanner_ws_id == scanner_ws_id:
                    return c
        return None
        

connections = Active_connections()


class Connection:
    connection_pair_counter = 0
    def __init__(self, username, viewer_ws_id):
        self.connection_pair_id = Connection.connection_pair_counter 
        self.username = username
        self.viewer_ws_id = viewer_ws_id
        self.scanner_ws_id = None
        Connection.connection_pair_counter = Connection.connection_pair_counter + 1
    
    def connect_scanner(self, scanner_ws_id):
        self.scanner_ws_id = scanner_ws_id
    
    
    def disconnect_scanner(self):
        self.scanner_ws_id = None
    
    def disconnect_viewer(self):
        connections.remove_connection(self.connection_pair_id)
    
    def click_photo(self):
        print ("Click Signal Received")
    
    def send_photo(self):
        print("Send photo")
    
    def receive_photo(self):
        print ("Photo Received")