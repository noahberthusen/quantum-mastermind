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
        self.initial_position = None
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
        self.solution = None
        self.backend = Aer.get_backend('statevector_simulator')
        self.results = []
        self.guess = []
        self.update_results()

    def available_gates(self, gate):
        s = 0
        for node in self.nodes:
            if (node.gate and node.gate.operator == gate):
                s += 1
        return self.gates[gate] - s

    def update_results(self):
        self.results = []
        self.guess = []
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
            if (np.array_equal(res.get_statevector(None, 3), [1, 0])): # 0 state
                self.results.append(arcade.color.BLACK)
                self.guess.append('0')
            elif (np.array_equal(res.get_statevector(None, 3), [1j, 0])): # 0 state
                self.results.append(arcade.color.BLACK)
                self.guess.append('0')  
            elif (np.array_equal(res.get_statevector(None, 3), [-1j, 0])): # 0 state
                self.results.append(arcade.color.BLACK)
                self.guess.append('0')
                
            elif (np.array_equal(res.get_statevector(None, 3), [0, 1])): # 1 state
                self.results.append(arcade.color.WHITE) 
                self.guess.append('1')
            elif (np.array_equal(res.get_statevector(None, 3), [0, -1])): # 1 state
                self.results.append(arcade.color.WHITE) 
                self.guess.append('1')
            elif (np.array_equal(res.get_statevector(None, 3), [0, 1j])): # 1 state
                self.results.append(arcade.color.WHITE)
                self.guess.append('1')
            elif (np.array_equal(res.get_statevector(None, 3), [0, -1j])): # 1 state
                self.results.append(arcade.color.WHITE)                
                self.guess.append('1')

            elif (np.array_equal(res.get_statevector(None, 3), [.707, .707])): 
                self.results.append(arcade.color.BLUE)
                self.guess.append('+')

            elif (np.array_equal(res.get_statevector(None, 3), [-.707, -.707])): 
                self.results.append(arcade.color.BLUE)
                self.guess.append('+')
                
            elif (np.array_equal(res.get_statevector(None, 3), [.707, -.707])): 
                self.results.append(arcade.color.RED)
                self.guess.append('-')
            elif (np.array_equal(res.get_statevector(None, 3), [-.707, .707])): 
                self.results.append(arcade.color.RED)
                self.guess.append('-')
            elif (np.array_equal(res.get_statevector(None, 3), [-.707j, .707j])): 
                self.results.append(arcade.color.RED)
                self.guess.append('-')
            elif (np.array_equal(res.get_statevector(None, 3), [.707j, -.707j])): 
                self.results.append(arcade.color.RED) 
                self.guess.append('-')
            # eventuall +i and -i
            else:
                self.results.append(arcade.color.BROWN)

class GameView(arcade.View):
    """ Main application class. """

    def __init__(self, level):
        super().__init__()

        arcade.set_background_color(arcade.color.GAINSBORO)

        self.button_list = None
        self.gate_list = None
        self.held_gate = None
        self.nodes_list = None
        self.circuit = None
        self.guesses = None
        self.solution = None
        self.won = False
        self.level = level

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """
        self.gate_list = arcade.SpriteList()
        self.button_list = arcade.SpriteList(is_static=True)
        self.wires_list = arcade.SpriteList(is_static=True)
        self.nodes_list = arcade.SpriteList(is_static=True)
        self.guesses = []

        # load in all UI buttons
        self.button_list.append(arcade.Sprite('./images/submit.png', 0.4, center_x=910, center_y=65))
        self.button_list.append(arcade.Sprite('./images/trash.png', 0.4, center_x=655, center_y=65))
        self.button_list.append(arcade.Sprite('./images/info.png', 0.4, center_x=900, center_y=480))
        self.button_list.append(arcade.Sprite('./images/exit.png', 0.4, center_x=950, center_y=480))


        # draw the 'circuitboard'
        for i in range(4):
            for j in range(3):
                node = Node(0.25) # node scale
                node.position = START_X + (i * 100), 150 + (j * 95)
                self.nodes_list.append(node)

        # load gates in here
        level_data = self.load_level(self.level)
        self.circuit = Circuit(self.nodes_list, level_data['gates'])
        self.solution = level_data['solution']


    def load_level(self, level):
        # read in a text file with the allowed gates
        with open('levels.json') as f:
            level_data = json.load(f)

            level = level_data[f'level{self.level}']

            for i in range(len(GATES)):
                for j in range(level['gates'][GATES[i]]):
                    gate = Gate(GATES[i], GATE_SCALE)
                    gate.position = 100, (80 + i*75)
                    gate.initial_position = gate.position
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
        arcade.draw_rectangle_filled(875, 270, 4, 330, arcade.color.BLACK)
        arcade.draw_rectangle_filled(800, 105, 330, 4, arcade.color.BLACK)

        # draw the guesses
        for i in range(len(self.guesses)):
            for j in range(4):
                arcade.draw_circle_filled(660 + (j * 56), 140 + (i * 53), 20, self.guesses[i][0][j])
            # draw the clues
            black, white = self.guesses[i][1]
            for j in range(black):
                arcade.draw_circle_filled(900 + (j * 20), 148 + (i * 53), 7, arcade.color.BLACK)
            for j in range(white):
                arcade.draw_circle_filled(900 + (j * 20), 128 + (i * 53), 7, arcade.color.WHITE)
            
        self.button_list.draw()
        self.wires_list.draw()
        self.nodes_list.draw()
        self.gate_list.draw()


    def on_mouse_press(self, x, y, button, key_modifiers):
        """ Called when the user presses a mouse button. """
        gates = arcade.get_sprites_at_point((x, y), self.gate_list)
        if len(gates) > 0:
            self.held_gate = gates[-1]

        buttons = arcade.get_sprites_at_point((x, y), self.button_list)
        if (buttons) :
            if (buttons[0] == self.button_list[0] and (not self.won)):
                if (not (sum([self.circuit.available_gates(GATES[i]) for i in range(len(GATES))]) == 0)): # you must use all the gates
                    pass
                else:
                    # check if all the gates are used
                    self.circuit.update_results()
                    # print('submit')
                    black_pegs = 0
                    white_pegs = 0
                    for color in ['0', '1', '+', '-']:
                        white_pegs += min(self.solution.count(color), self.circuit.guess.count(color))
                    for code_peg, guess_peg in zip(self.solution, self.circuit.guess):
                        if code_peg == guess_peg:
                            black_pegs += 1
                    white_pegs -= black_pegs
                    if (black_pegs == 4):
                        self.won = True
                        self.button_list.append(arcade.Sprite('./images/continue.png', 0.4, center_x=90, center_y=480))

                    self.guesses.append((self.circuit.results, (black_pegs, white_pegs)))

            elif (buttons[0] == self.button_list[1]):
                # print('trash')
                for gate in self.gate_list:
                    self.reset_gate(gate)
                self.circuit.update_results()
            elif (buttons[0] == self.button_list[2] and (not self.won)):
                # print('instructions')
                instruction_view = InstructionView(self.level)
                self.window.show_view(instruction_view)
            elif (len(self.button_list) == 5 and buttons[0] == self.button_list[4]):
                # print('continue')
                instruction_view = InstructionView(self.level + 1)
                self.window.show_view(instruction_view)


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
            self.reset_gate(self.held_gate)

        self.held_gate = None
        self.circuit.update_results()

    def reset_gate(self, gate):
        if (gate.node):
            gate.node.gate = None
            gate.node = None
        gate.position = gate.initial_position

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """ User moves mouse """
        if self.held_gate:
            self.held_gate.center_x += dx
            self.held_gate.center_y += dy

class InstructionView(arcade.View):
    def __init__(self, level):
        """ This is run once when we switch to this view """
        super().__init__()
        self.level = level
        self.texture = arcade.load_texture(f"./images/instructions{level}.png")

    """ View to show instructions for each level """
    # def on_show(self):
    #     arcade.set_background_color(arcade.csscolor.GAINSBORO)
    
    def on_draw(self):
        """ Draw this view """
        arcade.start_render()
        self.texture.draw_sized(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                                SCREEN_WIDTH, SCREEN_HEIGHT)

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, start the game. """
        game_view = GameView(self.level)
        game_view.setup()
        self.window.show_view(game_view)

def main():
    """ Main method """
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = InstructionView(1)
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()