# -*- coding: utf-8 -*-
"""resnet50_ages_final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1H48cA8EZyAKHNunY0FDuX6kArSs2ybGH

# Определение возраста покупателей

## Задача.

Сетевой супермаркет внедряет систему компьютерного зрения для обработки фотографий покупателей. Фотофиксация в прикассовой зоне поможет определять возраст клиентов, чтобы:

    Анализировать покупки и предлагать товары, которые могут заинтересовать покупателей этой возрастной группы;

    Контролировать добросовестность кассиров при продаже алкоголя.

## Загрузка и анализ данных

### Загрузим библиотеки
"""

import pandas as pd
import seaborn as sns
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator, array_to_img
from tensorflow.keras.preprocessing import image_dataset_from_directory

import tensorflow as tf
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.applications.resnet import ResNet50
from sklearn.metrics import mean_absolute_error

"""### Загрузим и проанализируем данные"""

path = "D:\\programs\\YA practicum\\AppaREAL"
data = pd.read_csv(path + '/labels.csv')
data.info()
print(data.head())

sns.displot(data = data['real_age'],
                   kind='hist',
                   bins = 100,
                   aspect = 1.4,
                   height = 8
                   )

    # Plot formatting
plt.title('распределение возраста в выборке')
plt.xlabel('возраст')
plt.ylabel('количество фотографий')
plt.xlim(0, 100)
plt.show()

# define train data generator
train_generator = ImageDataGenerator(validation_split = 0.25,
                                     width_shift_range=0.2,
                                     height_shift_range=0.2,
                                     rotation_range=90,
                                     horizontal_flip=True,
                                     rescale = 1/255).flow_from_dataframe(
                                                                            dataframe=data,
                                                                            directory=path + '/final_files',
                                                                            subset='training',
                                                                            x_col= 'file_name',
                                                                            y_col= 'real_age',
                                                                            target_size=(224, 224),
                                                                            batch_size=32,
                                                                            seed=12345,
                                                                            class_mode='raw'
                                                                            )

# функция загрузки тестовых данных
test_generator = ImageDataGenerator(validation_split = 0.25,
                                       rescale = 1/255).flow_from_dataframe(
                                                                            dataframe=data,
                                                                            directory=path + '/final_files',
                                                                            subset='validation',
                                                                            x_col= 'file_name',
                                                                            y_col= 'real_age',
                                                                            target_size=(224, 224),
                                                                            batch_size=(data['real_age'].count() - len(train_generator)),
                                                                            seed=12345,
                                                                            class_mode='raw'
                                                                            )

"""### Посмотрим фотографии"""

images, ages = next(train_generator)
for i in range (0,15):
    array = np.array(train_generator[0][0][i])
    plt.title(ages[i])
    plt.imshow(array)
    plt.grid ( False )
    plt.xticks([])
    plt.yticks([])
    plt.show()

images, ages = next(test_generator)
for i in range (0,15):
    array = images[i]
    plt.title(ages[i])
    plt.imshow(array)
    plt.grid ( False )
    plt.xticks([])
    plt.yticks([])
    plt.show()

"""### Промежуточный вывод: 
    Данные состоят из 7591 фотографии с лицами людей разных возрастов.
    Распределение возрастов нормальное, данные подходят для обучения.
    не много фотографий детей в районе 10 лет, так же заметны выбросы на круглых возрастах 20, 30, 40, 50, 60, 70, 80 и 90 лет.

## Создадим  и обучим модель

### Для удобства создадим фукнции
"""

# функция создания модели
def create_model(input_shape):
    optimizer = Adam(learning_rate = 0.0001)
    backbone = ResNet50(input_shape=input_shape,
                    classes = 1000,
                    weights='imagenet', 
                    include_top=False)

    model = Sequential()
    model.add(backbone)
    model.add(GlobalAveragePooling2D())
    model.add(Dense(1, activation='relu'))                
    model.compile(loss='mse', optimizer=optimizer, metrics=['mse'])

    return model

# функция обучения модели
def train_model(model, train_data, test_data, batch_size, epochs,
            steps_per_epoch, validation_steps):
    model.fit(train_data,
              validation_data=test_data,
              batch_size=batch_size, epochs=epochs,
              steps_per_epoch=steps_per_epoch,
              validation_steps=validation_steps,
              verbose=2)
    return model

"""### Создадим и обучим модель по функциям"""

resnet50 = create_model((224, 224, 3))

train_model(resnet50, train_generator, test_generator, 32, 10,
                None, None)

"""## Проведем предсказания для сохраненной и загруженной моделей

### Получим возраст из тестовых данных
"""

test_pics, test_ages = next(test_generator)

print(len(test_ages))
print('возраст из тестовой выборки', test_ages)

"""### Проведем предсказания полученной модели"""

# Предскажем по созданной модели
resnet50_predictions = resnet50.predict(test_generator)
print(len(resnet50_predictions))
print(resnet50_predictions)

mae = mean_absolute_error(test_ages, resnet50_predictions)
print('Ошибка обученной модели составила', mae)

sns.displot(data=resnet50_predictions,
            kind='hist',
            bins=100,
            aspect=1.5,
            height=8)
# Plot formatting
plt.title('распределение возраста в выборке')
plt.xlabel('возраст')
plt.ylabel('количество фотографий')
plt.xlim(0, 100)
plt.show()

"""### Сохраним модель, загрузим и проверим ее"""

resnet50.save('saved_model/RESNET50_trained.h5')

resne50_loaded = tf.keras.models.load_model('saved_model/RESNET50_trained.h5')

loaded_predict = resne50_loaded.predict(test_pics)

print(loaded_predict)
print(mean_absolute_error(test_ages, loaded_predict))

"""## Заключение

1. Для предсказания возраста по фотографии были предоставлены 7591 фотография людей разных возрастов.

        Распределение возрастов нормальное, данные подходят для обучения.
        Есть выбросы на круглых цифрах, блольше фотографий в возрасте 20, 30, 40, 50, 60, 70, 80 и 90 лет.

2. Для предсказания была выбрана модель Resnet50.
3. Предсказания проводились в 10 эпох, абсолютная ошибка составила 6,7 года.

        Модель сохранена для использования.
"""