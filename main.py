import multiprocessing
from multiprocessing import Queue
from yolo_detection import yolo_detection
from pygame_visualization import run_visualization
from ascii_window import run_ascii_window
import time

def main():
    multiprocessing.set_start_method('spawn', force=True)
    detection_queue = Queue()
    frame_queue = Queue(maxsize=1)  # Only keep the latest frame
    person_detected_queue = Queue()

    print("Starting YOLO detection...")
    yolo_process = multiprocessing.Process(target=yolo_detection, args=(detection_queue, frame_queue, person_detected_queue))
    yolo_process.start()

    print("Starting visualization process...")
    visualization_process = multiprocessing.Process(target=run_visualization, args=(detection_queue, person_detected_queue))
    visualization_process.start()

    print("Starting ASCII window process...")
    ascii_window_process = multiprocessing.Process(target=run_ascii_window, args=(frame_queue, person_detected_queue))
    ascii_window_process.start()

    print("All processes started. Waiting for completion...")
    
    try:
        yolo_process.join()
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Terminating processes...")
    finally:
        yolo_process.terminate()
        visualization_process.terminate()
        ascii_window_process.terminate()
        
        yolo_process.join()
        visualization_process.join()
        ascii_window_process.join()

    print("Main process exiting.")

if __name__ == "__main__":
    main()