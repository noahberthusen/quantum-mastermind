"""
Solitaire clone.
"""
import arcade
import json
import numpy as np
from qiskit import QuantumCircuit, execute, Aer

# Screen title and size
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 512
SCREEN_TITLE = "Quantum Mastermind"

# Constants for scaling
GATE_SCALE = 0.5
GATE_WIDTH = 50 * GATE_SCALE
GATE_HEIGHT = 50 * GATE_SCALE

BOTTOM_Y = 300
START_X = 230

GATES = ['H', 'Z', 'Y', 'X', 'CX']

class Gate(arcade.Sprite):
    """ Gate sprite """

    def __init__(self, operator, scale=1):
        """ Gate constructor """

        # Attributes for operator 
        self.operator = operator

        # Image for the sprite
        self.image_file_name = f'./images/{self.operator}.png'
        self.inital_position = None
        self.node = None

        super().__init__(self.image_file_name, scale)

class Node(arcade.Sprite):
    """ Circuit node sprite """

    def __init__(self, scale=1):
        self.image_file_name = './images/node.png'
        self.gate = None
        super().__init__(self.image_file_name, scale)

class Circuit():
    """ Class to keep track of used and unused gates """

    def __init__(self, nodes, gates):
        self.nodes = nodes
        self.gates = gates
        self.backend = Aer.get_backend('statevector_simulator')
        self.results = []
        self.update_results()

    def available_gates(self, gate):
        s = 0
        for node in self.nodes:
            if (node.gate and node.gate.operator == gate):
                s += 1
        return self.gates[gate] - s

    def update_results(self):
        arcade.finish_render()
        self.results = []
        circuits = []
        for i in range(4):
            qc = QuantumCircuit(1)
            for j in range(3):
                node = self.nodes[j + (3*i)]
                if (not node.gate):
                    pass
                else:
                    gate = node.gate
                    if (gate.operator == 'X'):
                        qc.x(0) # should be i
                    elif (gate.operator == 'Y'):
                        qc.y(0)
                    elif (gate.operator == 'Z'):
                        qc.z(0)
                    elif (gate.operator == 'H'):
                        qc.h(0)
            circuits.append(qc)
        
        for i in range(4):
            res = execute(circuits[i], self.backend).result()
            print(res.get_statevector())
            if (np.array_equal(res.get_statevector(), [0, 1])): # 0 state
                self.results.append(arcade.color.WHITE)
            else:
                self.results.append(arcade.color.BLACK)
        print(self.results)
        arcade.start_render()

class QMastermind(arcade.Window):
    """ Main application class. """

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Gate list
        self.gate_list = None

        arcade.set_background_color(arcade.color.GAINSBORO)

        self.held_gate = None
        self.nodes_list = None
        self.gui_list = None
        self.level = 1

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """
        self.gate_list = arcade.SpriteList()
        self.wires_list = arcade.SpriteList(is_static=True)
        self.nodes_list = arcade.SpriteList(is_static=True)

        # draw gate library


        # draw the 'circuitboard'
        for i in range(4):
            for j in range(3):
                node = Node(0.25) # node scale
                node.position = START_X + (i * 100), 150 + (j * 95)
                self.nodes_list.append(node)

        # load gates in here
        level_data = self.load_level(self.level)
        self.circuit = Circuit(self.nodes_list, level_data)

    def load_level(self, level):
        # read in a text file with the allowed gates
        with open('levels.json') as f:
            level_data = json.load(f)

            level = level_data[f'level{self.level}']

            for i in range(len(GATES)):
                for j in range(level[GATES[i]]):
                    gate = Gate(GATES[i], GATE_SCALE)
                    gate.position = 100, (80 + i*75)
                    gate.inital_position = gate.position
                    self.gate_list.append(gate)

        return level

    def on_draw(self):
        """ Render the screen. """
        # Clear the screen
        arcade.start_render()

        for i in range(4):
            arcade.draw_rectangle_filled(START_X + (i * 100), 250, 8, 300, arcade.color.SILVER)
        arcade.draw_rectangle_filled(90, 240, 120, 420, arcade.color.SILVER)
        arcade.draw_text('Gates', 55, 413, arcade.csscolor.BLACK, 22)

        arcade.draw_rectangle_filled(800, 240, 360, 420, arcade.color.SILVER)
        for i in range(4):
            arcade.draw_circle_filled(230 + (i * 100), 60, 25, arcade.color.BLACK)
            arcade.draw_circle_filled(230 + (i * 100), 440, 25, self.circuit.results[i])
        for i in range(5):
            arcade.Sprite('./images/empty.png', scale=0.3, center_x=100, center_y=(80+i*75)).draw()
        for i in range(len(GATES)):
            arcade.draw_text(f'x{self.circuit.available_gates(GATES[i])}', 45, 70+(i*75), arcade.color.BLACK, 16)

        self.wires_list.draw()
        self.nodes_list.draw()
        self.gate_list.draw()


    def on_mouse_press(self, x, y, button, key_modifiers):
        """ Called when the user presses a mouse button. """
        gates = arcade.get_sprites_at_point((x, y), self.gate_list)
        if len(gates) > 0:
            self.held_gate = gates[-1]

        # more

    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        """ Called when the user presses a mouse button. """
        if self.held_gate == None:
            return

        node, distance = arcade.get_closest_sprite(self.held_gate, self.nodes_list)
        reset_position = True
        if arcade.check_for_collision(self.held_gate, node):
            if (not node.gate):
                # update circuit in qiskit here
                if (self.held_gate.node):
                    self.held_gate.node.gate = None
                self.held_gate.position = node.center_x, node.center_y
                self.held_gate.node = node
                node.gate = self.held_gate
                reset_position = False

        if reset_position:
            if (self.held_gate.node):
                self.held_gate.node.gate = None
                self.held_gate.node = None
            self.held_gate.position = self.held_gate.inital_position

        self.held_gate = None
        self.circuit.update_results()


    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """ User moves mouse """
        if self.held_gate:
            self.held_gate.center_x += dx
            self.held_gate.center_y += dy


def main():
    """ Main method """
    window = QMastermind()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()