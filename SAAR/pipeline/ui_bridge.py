from core.state import AssistantState

def update_ui(state, orb, label):
    orb.set_state(state)

    if state == AssistantState.LISTENING:
        label.config(text="Listening...")
    elif state == AssistantState.THINKING:
        label.config(text="Thinking...")
    elif state == AssistantState.SPEAKING:
        label.config(text="Speaking...")
