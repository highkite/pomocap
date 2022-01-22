import json
import math
import pathlib
import logging

logger = logging.getLogger(__name__)

use_numpy = True
try:
    import numpy as np
except:
    use_numpy = False

# use fallback if use_numpy is false

NUM_MARKERS = 15
work_dir = pathlib.Path(__file__).parent.resolve()
DATA_FILE_PATH = f"{work_dir}/data.json"

data_initialized = False

meanwalker = None
genderaxis = None
weightaxis = None
nervousaxis = None
happyaxis = None
customaxis = None
body_parts = None

A = None


def load_data(file_path):
    global meanwalker
    global genderaxis
    global weightaxis
    global nervousaxis
    global happyaxis
    global customaxis
    global body_parts
    global data_initialized
    global A

    if data_initialized:
        return

    data = None
    with open(file_path, "r") as f:
        data = json.load(f)

    if not data:
        raise Exception(f"Could not find data file: {file_path}")

    meanwalker = data["meanwalker"]
    genderaxis = data["genderaxis"]
    weightaxis = data["weightaxis"]
    nervousaxis = data["nervousaxis"]
    happyaxis = data["happyaxis"]
    customaxis = data["customaxis"]

    if use_numpy:
        A = np.transpose(
            np.concatenate(
                (
                    np.array(meanwalker),
                    np.array(genderaxis),
                    np.array(weightaxis),
                    np.array(nervousaxis),
                    np.array(happyaxis),
                    np.array(customaxis),
                )
            ).reshape(6, len(meanwalker))
        )

    body_parts = data["body_parts"]
    data_initialized = True


class WalkerModel:
    structure_vertical_scale = 1
    structure_horizontal_scale = 1
    motion_vertical_scale = 1
    motion_horizontal_scale = 1

    walker_customness = 0
    phase = 0
    walker_initphase = 0

    X = None
    Y = None

    def __init__(
        self,
        walker_gender=1,
        walker_weight=1,
        walker_nervousness=1,
        walker_happiness=1,
        walker_speed=1,
        data_file_path=None,
    ):
        if not data_initialized:
            if data_file_path is not None:
                load_data(data_file_path)
            else:
                load_data(DATA_FILE_PATH)

        self.configure_model(
            walker_gender,
            walker_weight,
            walker_nervousness,
            walker_happiness,
            walker_speed,
        )

    def configure_model(
        self,
        walker_gender=1,
        walker_weight=1,
        walker_nervousness=1,
        walker_happiness=1,
        walker_speed=1,
    ):
        self.walker_gender = walker_gender
        self.walker_weight = walker_weight
        self.walker_nervousness = walker_nervousness
        self.walker_happiness = walker_happiness
        self.walker_speed = walker_speed

        if use_numpy:
            self.X = np.array(
                [
                    1,
                    6 * self.walker_gender,
                    6 * self.walker_weight,
                    6 * self.walker_nervousness,
                    6 * self.walker_happiness,
                    6 * self.walker_customness,
                ]
            )
            self.Y = np.matmul(A, self.X.T)

    def getFrequency(self):
        speed = meanwalker[NUM_MARKERS * 3]
        speed += self.walker_gender * genderaxis[NUM_MARKERS * 3]
        speed += self.walker_weight * weightaxis[NUM_MARKERS * 3]
        speed += self.walker_nervousness * nervousaxis[NUM_MARKERS * 3]
        speed += self.walker_happiness * happyaxis[NUM_MARKERS * 3]
        return speed / self.walker_speed

    def derive_pose_coordinates_numpy_matrix(self, walkertime):
        if A is None or self.X is None or self.Y is None:
            raise Exception("Data fields for numpy not correctly configured")

        int_val = walkertime + self.phase + self.walker_initphase * math.pi / 180
        sin_1 = math.sin(int_val)
        cos_1 = math.cos(int_val)
        sin_2 = math.sin(2 * int_val)
        cos_2 = math.cos(2 * int_val)

        V = np.hstack(
            (
                np.identity(46),
                sin_1 * np.identity(46),
                cos_1 * np.identity(46),
                sin_2 * np.identity(46),
                cos_2 * np.identity(46),
            )
        )

        res = np.matmul(V, self.Y)

        ret_val = []

        for i in range(NUM_MARKERS):
            ret_val.append(
                {
                    "x": res[i + NUM_MARKERS],
                    "y": res[i + 2 * NUM_MARKERS],
                    "z": res[i],
                    "part": body_parts[i],
                }
            )

        return ret_val

    def derive_pose_coordinates(self, walkertime):
        if use_numpy:
            logger.info("Use numpy mode")
            return self.derive_pose_coordinates_numpy_matrix(walkertime)
        else:
            logger.info("Use falback mode")
            return self.derive_pose_coordinates_fallback(walkertime)

    def derive_pose_coordinates_fallback(self, walkertime):
        values = []
        for i in range(NUM_MARKERS * 3 + 1):
            initialpos = meanwalker[i]
            initialpos += (
                genderaxis[i] * self.walker_gender
                + weightaxis[i] * self.walker_weight
                + nervousaxis[i] * self.walker_nervousness
                + happyaxis[i] * self.walker_happiness
                + customaxis[i] * self.walker_customness
            )

            motionpos = (
                (
                    meanwalker[i + (NUM_MARKERS * 3 + 1)]
                    + genderaxis[i + (NUM_MARKERS * 3 + 1)] * self.walker_gender
                    + weightaxis[i + (NUM_MARKERS * 3 + 1)] * self.walker_weight
                    + nervousaxis[i + (NUM_MARKERS * 3 + 1)] * self.walker_nervousness
                    + happyaxis[i + (NUM_MARKERS * 3 + 1)] * self.walker_happiness
                    + customaxis[i + (NUM_MARKERS * 3 + 1)] * self.walker_customness
                )
                * math.sin(
                    walkertime + self.phase + self.walker_initphase * math.pi / 180
                )
                + (
                    meanwalker[i + (NUM_MARKERS * 3 + 1) * 2]
                    + genderaxis[i + (NUM_MARKERS * 3 + 1) * 2] * self.walker_gender
                    + weightaxis[i + (NUM_MARKERS * 3 + 1) * 2] * self.walker_weight
                    + nervousaxis[i + (NUM_MARKERS * 3 + 1) * 2]
                    * self.walker_nervousness
                    + happyaxis[i + (NUM_MARKERS * 3 + 1) * 2] * self.walker_happiness
                    + customaxis[i + (NUM_MARKERS * 3 + 1) * 2] * self.walker_customness
                )
                * math.cos(
                    walkertime + self.phase + self.walker_initphase * math.pi / 180
                )
                + (
                    meanwalker[i + (NUM_MARKERS * 3 + 1) * 3]
                    + genderaxis[i + (NUM_MARKERS * 3 + 1) * 3] * self.walker_gender
                    + weightaxis[i + (NUM_MARKERS * 3 + 1) * 3] * self.walker_weight
                    + nervousaxis[i + (NUM_MARKERS * 3 + 1) * 3]
                    * self.walker_nervousness
                    + happyaxis[i + (NUM_MARKERS * 3 + 1) * 3] * self.walker_happiness
                    + customaxis[i + (NUM_MARKERS * 3 + 1) * 3] * self.walker_customness
                )
                * math.sin(
                    2
                    * (walkertime + self.phase + self.walker_initphase * math.pi / 180)
                )
                + (
                    meanwalker[i + (NUM_MARKERS * 3 + 1) * 4]
                    + genderaxis[i + (NUM_MARKERS * 3 + 1) * 4] * self.walker_gender
                    + weightaxis[i + (NUM_MARKERS * 3 + 1) * 4] * self.walker_weight
                    + nervousaxis[i + (NUM_MARKERS * 3 + 1) * 4]
                    * self.walker_nervousness
                    + happyaxis[i + (NUM_MARKERS * 3 + 1) * 4] * self.walker_happiness
                    + customaxis[i + (NUM_MARKERS * 3 + 1) * 4] * self.walker_customness
                )
                * math.cos(
                    2
                    * (walkertime + self.phase + self.walker_initphase * math.pi / 180)
                )
            )

            sum_val = initialpos + motionpos

            values.append(sum_val)

        ret_val = []

        for i in range(NUM_MARKERS):
            ret_val.append(
                {
                    "x": values[i + NUM_MARKERS],
                    "y": values[i + 2 * NUM_MARKERS],
                    "z": values[i],
                    "part": body_parts[i],
                }
            )

        return ret_val


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    wm = WalkerModel(
        data_file_path="/home/highway/Projekte/pose_detection/blender_addon/data.json"
    )
    print(wm.derive_pose_coordinates_numpy_matrix(1666))
    print(wm.derive_pose_coordinates_fallback(1666))
