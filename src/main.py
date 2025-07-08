import sys

import cv2

from src.common import logger
from src.janken_game import JankenGame


def check_system_requirements():
    required_packages = [
        ("cv2", "opencv-python"),
        ("mediapipe", "mediapipe"),
        ("pygame", "pygame"),
        ("OpenGL", "PyOpenGL"),
    ]

    missing_packages = []

    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            logger.info(f"✓ {package_name}")
        except ImportError:
            logger.info(f"✗ {package_name} (missing)")
            missing_packages.append(package_name)

    if missing_packages:
        logger.info(f"Missing packages: {', '.join(missing_packages)}")
        return False

    try:
        cap = cv2.VideoCapture(0)
        ret, _ = cap.read()
        cap.release()

        if ret:
            logger.info("✓ Camera available")
            return True
        else:
            logger.info("✗ Camera not available")
            return False
    except Exception as e:
        logger.info(f"✗ Camera check failed: {e}")
        return False


def main():
    try:
        game = JankenGame()
        game.run()
    except Exception as e:
        logger.info(f"Error running piano system: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_system_requirements()
    main()
