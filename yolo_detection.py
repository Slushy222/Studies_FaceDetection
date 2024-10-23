import cv2
import torch
import numpy as np
from queue import Empty as QueueEmpty

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5n', force_reload=False)
model = model.to('cpu')  # Force CPU usage

class DetectedObject:
    def __init__(self, bbox, class_id, confidence):
        self.bbox = bbox
        self.class_id = class_id
        self.confidence = confidence

def create_resizable_window():
    # Create a resizable window
    cv2.namedWindow('to be', cv2.WINDOW_NORMAL)
    # Get screen resolution
    screen = cv2.getWindowImageRect('to be')
    screen_width = screen[2]
    screen_height = screen[3]
    # Set initial window size to half the screen
    cv2.resizeWindow('to be', screen_width // 2, screen_height // 2)

def scale_frame(frame, window_size):
    """
    Scale the frame to fit the window while maintaining exact aspect ratio
    by adding black bars as needed (letterboxing/pillarboxing)
    """
    window_width, window_height = window_size
    frame_height, frame_width = frame.shape[:2]
    
    # Calculate target aspect ratios
    window_aspect = window_width / window_height
    frame_aspect = frame_width / frame_height
    
    if frame_aspect > window_aspect:
        # Image is wider than window - pillarbox
        new_width = window_width
        new_height = int(window_width / frame_aspect)
        scaled = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Add black bars on top and bottom
        top_bar = (window_height - new_height) // 2
        bottom_bar = window_height - new_height - top_bar
        final = cv2.copyMakeBorder(scaled, top_bar, bottom_bar, 0, 0, 
                                 cv2.BORDER_CONSTANT, value=(0, 0, 0))
    else:
        # Image is taller than window - letterbox
        new_height = window_height
        new_width = int(window_height * frame_aspect)
        scaled = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Add black bars on left and right
        left_bar = (window_width - new_width) // 2
        right_bar = window_width - new_width - left_bar
        final = cv2.copyMakeBorder(scaled, 0, 0, left_bar, right_bar, 
                                 cv2.BORDER_CONSTANT, value=(0, 0, 0))
    
    return final
def yolo_detection(detection_queue, frame_queue, person_detected_queue):
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    # Create resizable window
    create_resizable_window()
    
    while True:
        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            break

        # Get current window size
        window_rect = cv2.getWindowImageRect('to be')
        if window_rect is not None:
            window_width = window_rect[2]
            window_height = window_rect[3]
        else:
            # Default size if window rect not available
            window_width, window_height = 800, 600

        # Perform YOLOv5 detection
        results = model(frame)

        # Process YOLOv5 results
        detections = []
        person_detected = False
        for det in results.xyxy[0]:
            if det[4] > 0.5:  # Confidence threshold
                bbox = det[:4].cpu().numpy()
                class_id = int(det[5].cpu().numpy())
                confidence = float(det[4].cpu().numpy())
                detections.append(DetectedObject(bbox, class_id, confidence))

                if class_id == 0:  # Assuming 0 is the class_id for person
                    person_detected = True

        # Send detection results to the visualization process
        detection_queue.put(detections)

        # Send the current frame to the frame queue
        if frame_queue.empty():
            frame_queue.put(frame)
        else:
            try:
                frame_queue.get_nowait()  # Remove the old frame
                frame_queue.put(frame)  # Put the new frame
            except QueueEmpty:
                pass

        # Notify the ASCII window process about the person detection
        person_detected_queue.put(person_detected)

        # Display results with scaling
        frame_with_boxes = results.render()[0]
        # Scale the frame to fit the window
        scaled_frame = scale_frame(frame_with_boxes, (window_width, window_height))
        cv2.imshow('to be', scaled_frame)

        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('f'):  # Press 'f' to toggle fullscreen
            if cv2.getWindowProperty('to be', cv2.WND_PROP_FULLSCREEN) == cv2.WINDOW_FULLSCREEN:
                cv2.setWindowProperty('to be', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
            else:
                cv2.setWindowProperty('to be', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    cap.release()
    cv2.destroyAllWindows()