import os

from django.core.files.storage import FileSystemStorage


def raw_media_storage():
    # Storage for PDF, Excel, Word and other non-image files.
    # On Render (CLOUDINARY_CLOUD_NAME is set) files go to Cloudinary as raw files.
    # On your own computer (no Cloudinary variables) the normal media folder is used.
    if os.environ.get("CLOUDINARY_CLOUD_NAME"):
        from cloudinary_storage.storage import RawMediaCloudinaryStorage

        return RawMediaCloudinaryStorage()
    return FileSystemStorage()
