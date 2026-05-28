# Crear un ejecutable desde GitHub

Sí: esta versión incluye GitHub Actions para generar un `.exe` de Windows automáticamente.

## Qué hace

Cuando subes este repositorio a GitHub, el workflow:

```text
.github/workflows/build-windows-exe.yml
```

puede construir un ejecutable Windows usando PyInstaller.

El resultado queda como artefacto descargable:

```text
KMZ_3D_Volumenes_Windows.zip
```

Dentro de ese ZIP estará:

```text
KMZ_3D_Volumenes.exe
```

Al abrir el `.exe`, se levanta la aplicación en un servidor local y se abre el navegador.

---

## Cómo generar el ejecutable en GitHub

1. Sube todos los archivos de esta carpeta a un repositorio GitHub.
2. Entra al repositorio.
3. Abre la pestaña:

```text
Actions
```

4. Selecciona:

```text
Build Windows executable
```

5. Presiona:

```text
Run workflow
```

6. Espera que termine.
7. Entra al resultado del workflow.
8. Descarga el artefacto:

```text
KMZ_3D_Volumenes_Windows
```

9. Descomprime el ZIP.
10. Ejecuta:

```text
KMZ_3D_Volumenes.exe
```

---

## Opción para publicar una Release

También incluí:

```text
.github/workflows/release-windows-exe.yml
```

Si creas un tag tipo:

```text
v1.0.0
```

GitHub construirá el ejecutable y lo adjuntará a una Release.

---

## Importante

GitHub como página web no ejecuta Streamlit directamente. Hay dos formas correctas:

### 1. Aplicación web

Usar Streamlit Cloud conectado al repositorio.

### 2. Aplicación ejecutable

Usar GitHub Actions para generar el `.exe`.

Esta carpeta deja preparada la opción 2.
