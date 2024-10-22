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

def yolo_detection(detection_queue, frame_queue, person_detected_queue):
    # Initialize webcam
    cap = cv2.VideoCapture(0)

    while True:
        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            break

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

        # Display results
        frame_with_boxes = results.render()[0]
        cv2.imshow('YOLOv5 Detection', frame_with_boxes)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()