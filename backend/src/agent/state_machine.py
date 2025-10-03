from enum import Enum, auto

class AgentState(Enum):
    """
    The possivle states of Momentum agent during its execution workflow.
    """

    STARTING = auto()
    PLANNING = auto()
    CODE_GENERATION = auto()
    TESTING = auto()
    AWAITING_REVIEW = auto()
    FIXING = auto()
    DONE = auto()
    ERROR = auto()

class StateMachine:
    """
    Class to manage agents curr state. 
    """

    def __init__(self):
        self.curr_state = AgentState.STARTING
    
    def transition_to(self, new_state: AgentState):
        """
        Transitioning to a new state.
        """
        print(f"Transitioning from {self.curr_state} to {new_state}")
        self.curr_state = new_state

    def get_state(self) -> AgentState:
        """
        Get the current state.
        """
        return self.curr_state