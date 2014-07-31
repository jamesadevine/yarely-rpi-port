from state_machine import stateMachineFactory

handler_smf = StateMachineFactory()
handler_smf.add_state("Launching")
handler_smf.add_state("Idle")
handler_smf.add_state("Terminating")
handler_smf.add_state("Terminated")

handler_smf.add_transition("Launching", "Failed", "Terminating")
handler_smf.add_transition("Launching", "Registered", "Idle")
handler_smf.add_transition("Idle", "Stop", "Terminating")
handler_smf.add_transition("Terminating", "Stopped", "Terminated")

renderer_smf = StateMachineFactory(handler_smf)
renderer_smf.add_state("Preparing")
renderer_smf.add_state("Prepared")
renderer_smf.add_state("Becoming Visible")
renderer_smf.add_state("Visible")
renderer_smf.add_state("Becoming Invisible")
renderer_smf.add_state("Invisible")

renderer_smf.add_transition("Idle", "Prepare", "Preparing")
renderer_smf.add_transition("Preparing", "Prepared", "Prepared")
renderer_smf.add_transition("Prepared", "Become Visible", "Becoming Visible")
renderer_smf.add_transition("Becoming Visible", "Became Visible", "Visible")
renderer_smf.add_transition("Visible", "Become Invisible", "Becoming Invisible")
renderer.smf.add_transition("Becoming Invisible", "Became Invisible",
        "Invisible")
renderer.smf.add_transition("Invisible", "Prepare", "Preparing")
