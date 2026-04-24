class V10ActionEngine:
    def run(self, context):
        mission = context.get("mission")

        if not mission:
            return {"status": "idle"}

        step = mission.get("next_step")

        if not step:
            return {"status": "finished"}

        return {
            "status": "executed",
            "message": f"Executed step: {step}"
        }