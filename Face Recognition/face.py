import face_recognition.api as fr
import numpy as np
import os

def find_all_img(path):
    for path, dirs, files in os.walk(path):
        for file in files:
            if file[-3:] == 'jpg':
                yield((path,file))


def encode_img(img_path, data_path='./data'):
    """
    convert the imgs under the img_path into numpy ndarray.
    then save it in data_path
    """
    # read img and covert it
    title_list = []
    face_list = []
    img_name_list = []
    for i in img_path:
        for path, file in find_all_img(i):
            try:
                print(os.path.join(path, file))
                with open(os.path.join(path, path[path.rfind('/')+1:]+'.txt')) as f:
                    title = f.readline()
                img = fr.load_image_file(os.path.join(path, file))
                faces = fr.face_encodings(img)
                if faces:
                    for face in faces:
                        title_list.append(title)
                        face_list.append(face)
                        img_name_list.append(file)
            except:
                print("ERROR IMG!")
    
    # save file
    np_title_list = np.array(title_list)
    np_face_list = np.array(face_list)
    np_img_name_list = np.array(img_name_list)
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    np.save(os.path.join(data_path, 'title.npy'), np_title_list)
    np.save(os.path.join(data_path, 'face.npy'), np_face_list)
    np.save(os.path.join(data_path, 'img_name.npy'), np_img_name_list)
    


def load_img(data_path='./data'):
    if not os.path.exists(data_path):
        print('no such path')
        return
    np_title_list = np.load(os.path.join(data_path, 'title.npy'))
    np_face_list = np.load(os.path.join(data_path, 'face.npy'))
    np_img_name_list = np.load(os.path.join(data_path, 'img_name.npy'))
    return np_title_list, np_face_list, np_img_name_list

def compare_img(np_target, np_title_list, np_face_list, np_img_name_list, max_num=10):
    np_truth_list = fr.compare_faces(np_face_list, np_target)
    indices = np.where(np_truth_list)
    if indices:
        for i in range(min(max_num, len(indices))):
            title = np_title_list[indices[i]]
            img_name = np_img_name_list[indices[i]]
            print('Do you want to search: ', end='')
            print('title: ' + title.strip(), 'img_name: ' + img_name)
        # for i in range(len(np_truth_list)):
        #     if cnt >= max_num:
        #         break
        #     if np_truth_list[i] == True:

        #         cnt += 1
        #         print('Do you want to search: ', end='')
        #         print('title: ' + title.strip(), 'img_name: ' + img_name)
        # face = np_truth_list.index(True)
        # title = np_title_list[face]
        # img_name = np_img_name_list[face]
        # print('Do you want to search ', end='')
        # print(title, " ", img_name)
    else:
        print("Sorry, we've find no result.")


if __name__ == '__main__':
    encode_img(img_path=['./html_chinanews', './html_netease'])
    target = './messi.jpg'
    target = fr.load_image_file(target)
    target = fr.face_encodings(target)
    np_title_list, np_face_list, np_img_name_list = load_img()
    compare_img(target, np_title_list, np_face_list, np_img_name_list, 20)