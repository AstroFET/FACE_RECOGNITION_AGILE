import face_recognition
import cv2
import numpy as np
import platform 
import os , sys
import psutil
import pickle
import math
import argparse
WINDOW_NAME = 'face_Recognition'
filename = "face_database.dat"
path= '/home/tky/dlib-19.17/face_training'

def parse_args():
    # Parse input arguments
    desc = 'Jetson Nano Video capture arg descriptions'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--rtsp', dest='use_rtsp',
                        help='use IP CAM (remember to also set --uri)',
                        action='store_true')
    parser.add_argument('--uri', dest='rtsp_uri',
                        help='RTSP URI, e.g. rtsp://192.168.1.64:554',
                        default='rtsp://192.168.0.150:554/stream', type=str)
    parser.add_argument('--latency', dest='rtsp_latency',
                        help='latency in ms for RTSP [200]',
                        default=200, type=int)
    parser.add_argument('--jet', dest="use_jet",
                        help='output CSI camera on the nano dev kit', 
                        action='store_true')
    parser.add_argument('--vid', dest='video_dev',
                        help='device # of USB webcam (/dev/video?) [1]',
                        default=1, type=int)
    parser.add_argument('--width', dest='image_width',
                        help='image width [1920]',
                        default=1920, type=int)
    parser.add_argument('--height', dest='image_height',
                        help='image height [1080]',
                        default=1080, type=int)
    args = parser.parse_args()
    
    return args


def open_cam_rtsp(uri, width, height, latency):
    gst_str = ('rtspsrc location={} latency={} ! '
               'rtph264depay ! h264parse ! omxh264dec ! '
               'nvvidconv ! '
               'video/x-raw, width=(int){}, height=(int){}, '
               'format=(string)BGRx ! '
               'videoconvert ! appsink').format(uri, latency, width, height)
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)



def jetson_nano(capture_width=1280, capture_height=720, display_width=720, display_height=720, framerate=58, flip_method= 2):
#Return an OpenCV-compatible video source description 
#that uses gstreamer to capture video from the camera on a #Jetson Nano
#code sets up video stream to the jetson camera instead of using the default webcam
    
    return cv2.VideoCapture(f'nvarguscamerasrc ! video/x-raw(memory:NVMM), ' +
                            f'width=(int){capture_width}, height=(int){capture_height}, '+ 
                            f'format=(string)NV12, framerate=(fraction){framerate}/1 ! ' +
                            f'nvvidconv flip-method={flip_method} ! '+  
                            f'video/x-raw, width=(int){display_width}, height=(int){display_height},format=(string)BGRx ! '+  
                             'videoconvert ! video/x-raw, format=(string)BGR ! appsink'
                             ,cv2.CAP_GSTREAMER)


def open_window(width, height):
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, width, height)
    cv2.moveWindow(WINDOW_NAME, 12, 12 )
    cv2.setWindowTitle(WINDOW_NAME, 'jetson')


def Get_user_information():
#Name: Get_user_information
#Description: This function first checks for a fwhen the file is found the binary data is then unpickled which converts binary data back into python objects. 
#Next the function asks if you want to upload another client to the system.
# The input takes in the the clients name stores it in known_face_names. Next the name is appended with".jpeg" and the picture is loaded into the program
# Next the facial recognition information is gathered using "face_recognition.face_encodings".
# Finally the encoding facial data is stored in "known_face_encodings"
# This data will then be re-pickled and stored back in the binary file   
    if bool(input("load new data into program type anything:")):
        try:
          #os.path.exists(filename):
            with open( filename, 'rb') as pickle_in:
                 known_face_encodings,known_face_names = pickle.load(pickle_in)
        except FileNotFoundError:   
                 print("file doesn't exist")
        #Changes directory to the imagefile folder 
        os.chdir(path)
        print(os.getcwd())

        #Gets image list names
        Imagefiles= os.listdir()

        # For loop goes through folder ,grabs the image files and get the encoding name data
        for name in Imagefiles:   
            display_pictures[index]= cv2.imread(name,0)                                           
            known_face_names.append(name)
            file_image = face_recognition.load_image_file(name)
            user_face_encoding = face_recognition.face_encodings(file_image)[0]
            known_face_encodings.append(user_face_encoding)

       #Save the facecoding data and name to the database  
        saveClient(known_face_encodings,known_face_names)


def Load_client_database():
#Name:Load_client_database
#Description: Opens client data base file and stores the information in "encoding" and "names"
    with open( filename, 'rb') as pickle_in:  
        (encoding, names) = pickle.load(pickle_in)
    return (encoding,names)


def saveClient(e,n):
#Name: SaveClient information 
#Description: This function pickles and then saves the facial encoding data and face name to a binary file.
#The function takes in known_facial_encodings , and known_face_names as data.
   os.chdir("/home/tky/dlib-19.17")           
   with open(filename, "wb") as face_data_file:
        face_data = [ e,n]
        pickle.dump(face_data, face_data_file)



def read_cam(cap):
    process_this_frame =True
    face_locations = []
    face_encodings = []
    show_help = True
    full_scrn = False
    help_text = '"Esc" to Quit, "H" for Help, "F" to Toggle Fullscreen'
    font = cv2.FONT_HERSHEY_DUPLEX
    name=""
  
    while True:

        _, img = cap.read() # grab the next image frame from camera
        if cv2.getWindowProperty(WINDOW_NAME, 0) < 0:
            # Check to see if the user has closed the window
            # If yes, terminate the program
            break
        if show_help:
           cv2.putText(img, help_text, (11, 20), font,
                       1.0, (32, 32, 32), 4, cv2.LINE_AA)
           cv2.putText(img, help_text, (10, 20), font,
                       1.0, (240, 240, 240), 1, cv2.LINE_AA)
        reduced_frames = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = reduced_frames[:, :, ::-1]
        if process_this_frame: 
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []
            display=[]
            
            for face_encoding in face_encodings:
               face_distances =face_recognition.face_distance(known_face_encodings,face_encoding)
               best_match_index = np.argmin(face_distances)
               conVal= (1.38 - face_distances[best_match_index])*100
               matchp = str(float("{0:.2f}".format(conVal)))
               if face_distances[best_match_index] <.59:
                   name = known_face_names[best_match_index]+":"+matchp+'%'   
                   
               else:
                   name="Unknown"

               face_names.append(name)
            for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
               top *= 4
               right *= 4
               bottom *= 4
               left *= 4
                
               cv2.rectangle(img, (left, top), (right,bottom), (255, 0, 255), 2)
                
                # Draw a label with a name below the face
               cv2.rectangle(img, (left, bottom - 25), (right, bottom), (0, 0, 255), cv2.FILLED)
               font = cv2.FONT_HERSHEY_DUPLEX
               cv2.putText(img, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
              # cv2.putText(img,matchp, (left + 12, bottom - 30), font, 1.0, (0, 255, 255), 1)
       
        cv2.imshow(WINDOW_NAME, img)
        key = cv2.waitKey(10)

        if key == 27: # ESC key: quit program
            break
        elif key == ord('H') or key == ord('h'): # toggle help message
            show_help = not show_help
        elif key == ord('F') or key == ord('f'): # toggle fullscreen
            full_scrn = not full_scrn
            if full_scrn:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND)

def main():
    args = parse_args()
    print('Called with args:')
    print(args)
    print('OpenCV version: {}'.format(cv2.__version__))
    
    if args.use_rtsp:
        cap = open_cam_rtsp(args.rtsp_uri, args.image_width,args.image_height, args.rtsp_latency)
    elif args.use_jet:
        cap = jetson_nano()
    else:
        cap = cv2.VideoCapture(0)
        
    open_window(args.image_width, args.image_height)
    read_cam(cap)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    Get_user_information()
    print("Known faces backed up to disk.")
    known_face_encodings,known_face_names =Load_client_database()
   
    main()     
