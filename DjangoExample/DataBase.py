import os.path
import random
import re
import sqlite3
import string
from cryptocode.myfunctions import *


class Archivo:

    def __init__(self, archivo, key=None):
        self.archivo = archivo
        self.__key = key

    def leer(self):
        with open(self.archivo, "rb") as archivo:
            data = b64decode(archivo.read()).decode()
            if self.__key:
                return decrypt(data, self.__key)
            else:
                return data

    def escribir(self, data):
        with open(self.archivo, "wb") as archivo:
            data = str(data)
            if self.__key:
                data = encrypt(data, self.__key)
            archivo.write(b64encode(data.encode()))


def manejo_excepciones(funcion):
    def funcion_modificada(*args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except Exception as e:
            print(f'Manejo de exepciones: {e}')
    return funcion_modificada


def generar_caracteres_aleatorios(longitud):
    return ''.join(
        random.choices(string.ascii_letters + string.digits + string.punctuation, k=int(longitud)))


def generar_usuario(longitud):
    letras = 'bcdfghjklmnprstvwxyz'
    vocales = 'aeiou'
    usuario = random.choice(letras).upper()  # Elegir una letra inicial y convertirla a mayúscula
    longitud -= 1  # Restar 1 para tener en cuenta la letra inicial

    for i in range(longitud):
        if i % 2 == 0:  # Alternar entre consonantes y vocales
            usuario += random.choice(vocales)
        else:
            usuario += random.choice(letras)
    return usuario


def extraer_usuario_de_correo(correo):
    patron = r"([^@]+)@.*"
    coincidencia = re.match(patron, correo)
    if coincidencia:
        return coincidencia.group(1).capitalize()
    else:
        return None


class DB:
    __conexion = None

    def __init__(self, base_datos, key='hfNdd521@Dfkl'):
        """
        El parametro 'key' encripta el archivo que contiene la clave de cifrado generada automaticamente '*.key',
        la cual se utiliza para cifrar los campos llamados 'password' en la base de datos,el uso de este
        parametro es obligatorio para almacenar una clave de manera segura.

        Puedes asignar un key personalizado al momento de instanciar la clase. Si se elimina el archivo con la clave
        generada, los campos cifrados no podran ser leidos. Al momento de obtener un campo cifrado deberas usar el
        metodo 'descifrar' para poder leerlo. Tambien puedes cifrar datos antes de ser enviados a la base de datos.
        """
        if '.db' not in base_datos:
            base_datos += '.db'
        self.__base_datos = base_datos
        self.__key = key
        self.__conexion = self.conectar_base_datos()

    @manejo_excepciones
    def __obtener_clave(self):
        archivo_key = Archivo(self.__base_datos.replace('.db', '.key'), self.__key)
        if os.path.exists(archivo_key.archivo):
            return archivo_key.leer()
        else:
            # Si la clave no existe se genera una nueva y se guarda en el archivo externo
            clave = generar_caracteres_aleatorios(len(self.__key) ** 1.5)
            archivo_key.escribir(clave)
            return clave

    @manejo_excepciones
    def conectar_base_datos(self):
        if self.__conexion:
            self.__conexion.close()
        return sqlite3.connect(self.__base_datos)

    @property
    def base_datos(self):
        return self.__base_datos

    @manejo_excepciones
    def crear_tabla(self, nombre_tabla, campos):
        cursor = self.__conexion.cursor()
        campos_str = ', '.join([f'{nombre} {tipo}({longitud})' for nombre, tipo, longitud in campos])
        cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {nombre_tabla} (id INTEGER PRIMARY KEY AUTOINCREMENT, {campos_str})')
        self.__conexion.commit()

    @manejo_excepciones
    def insertar_registro(self, nombre_tabla, datos):
        cursor = self.__conexion.cursor()
        campos = ', '.join(datos.keys())
        valores = ', '.join(['?'] * len(datos))
        for i in datos:
            if i.lower().__eq__('password'):
                datos[i] = self.cifrar(datos[i])
        cursor.execute(f'INSERT INTO {nombre_tabla} ({campos}) VALUES ({valores})', list(datos.values()))
        self.__conexion.commit()

    @manejo_excepciones
    def actualizar_registro(self, nombre_tabla, id_registro, nuevos_datos):
        cursor = self.__conexion.cursor()
        for i in nuevos_datos:
            if i.lower().__eq__('password'):
                nuevos_datos[i] = self.cifrar(nuevos_datos[i])
        nuevos_datos_str = ', '.join([f'{nombre} = ?' for nombre in nuevos_datos.keys()])
        cursor.execute(f'UPDATE {nombre_tabla} SET {nuevos_datos_str} WHERE id = ?',
                       list(nuevos_datos.values()) + [id_registro])
        self.__conexion.commit()

    @manejo_excepciones
    def obtener_registro_por_valor(self, nombre_tabla, nombre_columna, valor):
        cursor = self.__conexion.cursor()
        cursor.execute(f'SELECT * FROM {nombre_tabla} WHERE {nombre_columna} = ?', [valor])
        columnas = [col[0] for col in cursor.description]
        registros = cursor.fetchall()
        resultado = []
        for registro in registros:
            resultado.append({columnas[i]: registro[i] for i in range(len(columnas))})
        return resultado

    @manejo_excepciones
    def obtener_registro_por_id(self, nombre_tabla, id_registro):
        cursor = self.__conexion.cursor()
        cursor.execute(f'SELECT * FROM {nombre_tabla} WHERE id = ?', [id_registro])
        columnas = [col[0] for col in cursor.description]
        registro = cursor.fetchone()
        if registro:
            return {columnas[i]: registro[i] for i in range(len(columnas))}
        else:
            return None

    @manejo_excepciones
    def eliminar_campo(self, nombre_tabla, nombre_campo):
        cursor = self.__conexion.cursor()
        cursor.execute(f'ALTER TABLE {nombre_tabla} DROP COLUMN {nombre_campo}')
        self.__conexion.commit()

    @manejo_excepciones
    def eliminar_registro_por_id(self, nombre_tabla, id_registro):
        cursor = self.__conexion.cursor()
        cursor.execute(f'DELETE FROM {nombre_tabla} WHERE id = ?', [id_registro])
        self.__conexion.commit()

    @manejo_excepciones
    def desconectar(self):
        if self.__conexion:
            self.__conexion.close()
            self.__conexion = None
        else:
            ValueError('La conexion no existe')

    def generar_correo(self, tabla, campo='email'):
        while True:
            correo = generar_usuario(5).lower() + '@example.com'
            cursor = self.__conexion.cursor()
            try:
                # Se comprobara que el correo generado no exista en la base de datos, las excepciones aqui
                # indican que no se encontro la tabla o el correo buscado.
                cursor.execute(f'SELECT * FROM {tabla} WHERE {campo} = ?', [correo])
            except Exception as e:
                print(f'Generador de correos ({self.base_datos})...{e}')
                pass
            if not cursor.fetchone():
                return correo

    def cifrar(self, dato):
        return encrypt(dato, self.__obtener_clave())

    def descifrar(self, dato):
        return decrypt(dato, self.__obtener_clave())


"""
# Ejemplo de uso:
base_datos = DB('prueba.db')

campos = [('nombre', 'TEXT', 50), ('apellido', 'TEXT', 50), ('edad', 'INTEGER', 50), ('email', 'TEXT', 100),
          ('password', 'TEXT', 100)]
base_datos.crear_tabla('usuarios', campos)

correo = base_datos.generar_correo('usuarios')
usuario = extraer_usuario_de_correo(correo)
base_datos.insertar_registro('usuarios', {'nombre': usuario, 'apellido': 'nunez', 'edad': 20, 'email': correo,
                                          'password': '5252525252'})

# Devuelve una lista que contiene los registros, cada registro es un diccionario
registros = base_datos.obtener_registro_por_valor('usuarios', 'apellido', 'nunez')
print('Los registros obtenidos por sus valores son', registros)

for i in registros:
    # i sera igual a un diccionario, este contiene los datos del registro obtenido
    print(i)
    id_nuevo_registro = i['id']
    pas = base_datos.descifrar(i['password'])
    print('La contraseña cifrada: ' + i['password'])
    print('La contraseña descifrada es: ' + pas)
    base_datos.actualizar_registro('usuarios', id_nuevo_registro, {'edad': 41, 'password': '42424242'})
    registro_obtenido = base_datos.obtener_registro_por_id('usuarios', id_nuevo_registro)
    print("Registro obtenido por ID:", registro_obtenido)
    print('La contraseña cifrada: ' + registro_obtenido["password"])
    pas = base_datos.descifrar(registro_obtenido["password"])
    print('La contraseña descifrada es: ' + pas)

base_datos.desconectar()
"""
