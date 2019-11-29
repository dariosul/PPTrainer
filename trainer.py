import threading
import time


class SharedState(object):
    """
    This will be stuff like the inference result and motor state, which
    get used by the DecisionMaker.
    """
    def __init__(self):
        self._camera_inference_result = 0
        self._motor_target_value = {0,0,0}

        self._camera_listeners = []
        self._motor_listeners = []

    def on_person_detected(self, value):
        self._camera_inference_result = value
        # pretend that new_camera_data % 10 == 0 is equivalend to person detected
        if value % 10 == 0:
            for listener in self._camera_listeners:
                listener()

    def set_target_motor_state(self, value):
        self._motor_target_value = value
        for listener in self._motor_listeners:
            listener()

    def get_camera_data(self):
        return self._camera_inference_result

    def get_target_motor_state(self):
        return self._motor_target_value

    def register_camera_listener(self, listener):
        self._camera_listeners.append(listener)

    def register_motor_listener(self, listener):
        self._motor_listeners.append(listener)


class DecisionMaker(object):
    def __init__(self, shared_state):
        self._shared_state = shared_state
        self._shared_state.register_camera_listener(self.decide_how_to_move)

    def decide_how_to_move(self):
        # Put decision logic here.
        print("DecisionMaker: received new camera data. Processing...")
        inference_result = self._shared_state.get_camera_data()
        new_motor_data = {0,0,0}
        self._shared_state.set_target_motor_state(new_motor_data)


class Camera(object):
    def __init__(self, shared_state):
        self._shared_state = shared_state
        self._continue_streaming = False
        self._thread = threading.Thread(target=self._read_data)
        self._thread.daemon = True
        self._thread.start()

    def start_streaming(self):
        self._continue_streaming = True

    def stop_streaming(self):
        self._continue_streaming = False

    def _read_data(self):
        while True:
            if not self._continue_streaming:
                continue
            time.sleep(2)
            # just multiply the old number by two pretending you got new data
            new_camera_data = 2 + self._shared_state.get_camera_data()
            print("Camera: received new data: ", new_camera_data)
            self._shared_state.on_person_detected(new_camera_data)
    #
    # def _on_new_camera_data(self):
    #     new_camera_data = 2 * self._shared_state.get_camera_data()
    #     print("Camera: received new data: {new_camera_data}")
    #     self._shared_state.update_camera_data(new_camera_data)


class MotorController(object):
    """
    Uses PySerial to interface with Arduino
    """
    def __init__(self, shared_state):
        self._shared_state = shared_state
        self._shared_state.register_motor_listener(self.move_motors)

    def move_motors(self ):
        target = self._shared_state.get_target_motor_state()
        # TODO: use PySerial to send motor commands
        # read back actual motor values into shared_state
        print("MotorController: moved motors to {target}")


class MainApp(object):
    START_COMMAND = "start"
    STOP_COMMAND = "stop"

    def __init__(self, camera, decision_maker, motor_controller):
        self._camera = camera
        self._decision_maker = decision_maker
        self._motor_controller = motor_controller

    def run(self):
        while True:
            command = input()
            self.process_command(command)

    def process_command(self, command):
        if command == self.START_COMMAND:
            self.start_trainer()
        elif command == self.STOP_COMMAND:
            self.stop_trainer()
        else:
            print("Unknown command {command}")

    def start_trainer(self):
        print("Starting the trainer.")
        self._camera.start_streaming()

    def stop_trainer(self):
        print("Stopping the trainer.")
        self._camera.stop_streaming()


def main():
    shared_state = SharedState()
    camera = Camera(shared_state)
    decision_maker = DecisionMaker(shared_state)
    motor_controller = MotorController(shared_state)

    main_app = MainApp(camera, decision_maker, motor_controller)
    main_app.run()


if __name__ == "__main__":
    main()
