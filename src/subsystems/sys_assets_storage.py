from datetime import timedelta
from os import remove
from random import choice
from typing import List

from firebase_admin import storage
from google.cloud.storage.blob import Blob

from config import PROJ_CACHE_PATH
from log import Logger

from ..utils.helper import Helper


class AssetsStorage:
    """ 
    Cloud storage containing static assets (i.e audio files, images, etc.) 

    This would help reduce the size of the project when deploying to a server and
    decrease deployment time.

    TODO: Update function annotations for each class method
    """

    # If the file type matches the category, attach
    # the prefix containing the category name to the
    # file name passed
    CATEGORIES = {
        ('mp3', 'wav', 'ogg'): 'audio',
        ('mp4', 'webm', 'mov', 'avi'): 'videos',
        ('png', 'jpg', 'jpeg', 'gif'): 'images'
    }

    def __init__(self) -> None:
        self._storage_bucket = storage.bucket()
        self.class_name = __class__.__name__
        self._audio_cache_path = f"{PROJ_CACHE_PATH}/{self.class_name}"
        self._audio_file_path = ""

    def remove_audio_file(self):
        """ Removes the file stored at this path. """
        remove(self.audio_file_path)

    def _get_folder_category(self, file_name: str):
        """
        Gets the folder category for a particular file

        NOTE: Google's Cloud Storage operates with a flat namespace 
        (no hierarchical file structure). The '/' prefix emulates
        the file hierarchy.
        See more: https://cloud.google.com/storage/docs/folders
        """
        file_ext = Helper.get_file_extension(file_name)
        file_ext = file_ext.lower().replace(".", "")
        for file_extensions in self.CATEGORIES:
            if file_ext in file_extensions:
                return self.CATEGORIES.get(file_extensions)

    def validate_filename(self, filename: str) -> bool:
        """ 
        Validates filename before uploading to GCS 

        See full list of conditions for appropiate filenames:
        https://cloud.google.com/storage/docs/objects#naming
        """
        invalid_substrings = ['\r', '\n', '#', '[', ']', '*',
                              '?', ':', '"', '<', '>', '|']
        if filename == '.' or filename == '..':
            return False
        if filename.startswith(".well-known/acme-challenge/"):
            return False
        if any([substr in filename for substr in invalid_substrings]):
            return False
        return True

    def get_blob(self, blob_name: str) -> Blob:
        blob = self._storage_bucket.blob(blob_name)
        return blob

    def upload_from_memory(self, contents, dst_blob_name: str,
                           content_type: str = "text/plain") -> None:
        """
        See full list of content types or media types here:
        https://en.wikipedia.org/wiki/Media_type#Common_examples
        """
        category = self._get_folder_category(file_name=dst_blob_name)
        if category is None:
            blob_name = dst_blob_name
        else:
            blob_name = f"{category}/{dst_blob_name}"
        blob = self.get_blob(blob_name)
        blob.upload_from_string(contents, content_type=content_type)

    def download_to_file_with_name(self, blob_name: str, filename: str):
        """ 
        Gets blob from GCS and downloads it onto file with name: 
        filename. Use this if given the name of the blob, not the blob
        itself.
        """
        blob = self.get_blob(blob_name)
        blob.download_to_filename(filename)

    def download_blob_to_file(self, blob: Blob, filename: str):
        """ 
        Downloads blob from GCS onto file with name: filename, if given blob
        at firsthand. This helps reduce additional calls to GCS if blob is already
        provided.
        """
        blob.download_to_filename(filename)

    def download_audio_file(self, blob: Blob, audio_clip_name: str) -> None:
        """ Writes an audio file to disk given its path. """
        Helper.mksubdir(PROJ_CACHE_PATH, self.class_name)
        self.audio_file_path = f"{self.audio_cache_path}/{audio_clip_name}"
        self.download_blob_to_file(blob, self.audio_file_path)

    def get_audio_file(self, audio_clip_name: str) -> bool:
        """ 
        Gets audio blob from GCS if only given the name of 
        the audio file. If given the blob and one wants to download
        it, use download_audio_file().
        """
        blobs = self.get_blobs(prefix="audio/", return_as_list=True)
        filename, blob = self.search_for_blob(blobs, audio_clip_name)
        if not filename and not blob:
            Logger.ERROR(f"Audio clip {audio_clip_name} not found.")
            return False
        self.download_audio_file(blob, filename)
        return True

    @property
    def audio_file_path(self):
        return self._audio_file_path

    @audio_file_path.setter
    def audio_file_path(self, path: str):
        self._audio_file_path = path

    @property
    def audio_cache_path(self):
        return self._audio_cache_path

    def delete_obj(self, blob_name: str) -> bool:
        """
        Source: 
        https://cloud.google.com/storage/docs/deleting-objects#storage-delete-object-python
        """
        blob = self._storage_bucket.blob(blob_name)

        # Optional: set a generation-match precondition to avoid potential race conditions
        # and data corruptions. The request to delete is aborted if the object's
        # generation number does not match your precondition.
        # Fetch blob metadata to use in generation_match_precondition.
        blob.reload()
        generation_match_precondition = blob.generation
        blob.delete(if_generation_match=generation_match_precondition)
        return True

    def rename_obj(self, old_blob_name: str, new_blob_name: str):
        blob = self.get_blob(old_blob_name)

        # Optional: set a generation-match precondition to avoid potential race conditions
        # and data corruptions. The request is aborted if the object's
        # generation number does not match your precondition. For a destination
        # object that does not yet exist, set the if_generation_match precondition to 0.
        # If the destination object already exists in your bucket, set instead a
        # generation-match precondition using its generation number.
        # There is also an `if_source_generation_match` parameter, which is not used in this example.
        destination_generation_match_precondition = 0

        self._storage_bucket.copy_blob(
            blob=blob,
            destination_bucket=self._storage_bucket,
            new_name=new_blob_name,
            if_generation_match=destination_generation_match_precondition)
        self._storage_bucket.delete_blob(old_blob_name)

    def get_blobs(self, prefix: str = None, delimiter: str = None,
                  return_as_list: bool = False):
        """ 
        "Lists all the blobs in the bucket that begin with the prefix.

        This can be used to list all blobs in a "folder", e.g. "public/".

        The delimiter argument can be used to restrict the results to only the
        "files" in the given "folder". Without the delimiter, the entire tree under
        the prefix is returned. 

        For example, given these blobs:

            a/1.txt
            a/b/2.txt

        If you specify prefix ='a/', without a delimiter, you'll get back:

            a/1.txt
            a/b/2.txt

        However, if you specify prefix='a/' and delimiter='/', you'll get back
        only the file directly under 'a/':

            a/1.txt

        As part of the response, you'll also get back a blobs.prefixes entity
        that lists the "subfolders" under `a/`:

            a/b/
        "

        Source for comments above:     
        https://cloud.google.com/storage/docs/listing-objects#storage-list-objects-python
        """
        iterator = self._storage_bucket.list_blobs(
            prefix=prefix,
            delimiter=delimiter
        )
        if return_as_list:
            blobs = [blob for blob in iterator]
            return blobs
        return iterator

    def list_blobs_as_str(self, prefix: str):
        """ Gets all the blobs for a specific prefix, then prepare a list
        to send to the users. """
        prefix_path = f"{prefix}/"
        blobs = self.get_blobs(
            prefix=prefix_path, return_as_list=True)
        directories = self._get_directories(prefix_path)
        directories_in_path = blobs_paths = ""
        counter = counter2 = 0
        for blob in blobs:
            # Remove the upmost parent folder from its name
            name = blob.name.replace(prefix_path, "")
            blob_ext = Helper.get_file_extension(name)
            if (blob_ext is not None) and ('/' not in name):
                name = Helper.get_name(name)
                counter += 1
                blobs_paths += f"{counter}) {name}\n"
        for folder in directories:
            counter2 += 1
            folder = folder.replace(prefix_path, "")
            directories_in_path += f"{counter2}) {folder}\n"
        return blobs_paths, directories_in_path

    def _get_directories(self, prefix: str) -> set:
        """
        Gets directories in a bucket.

        Source: 
        https://github.com/GoogleCloudPlatform/google-cloud-python/issues/920 
        """
        iterator = self.get_blobs(prefix=prefix, delimiter='/')
        prefixes = set()
        for page in iterator.pages:
            prefixes.update(page.prefixes)
        return prefixes

    def list_bucket_directories_as_str(self, prefix: str = None) -> str:
        """ Lists the bucket directories in a string. """
        message = "\n"
        directories = self._get_directories(prefix=prefix)
        for i, directory in enumerate(directories):
            count = i + 1
            message += f"{count}) {directory}\n"
        return message

    def search_for_blob(self, blobs: List[Blob], blob_to_search: str):
        """ 
        Searches for a blob with blob_to_search. Mainly used to 
        encapsulate logic when attempting to play an audio clip
        from GCS through Discord commands. Returns the filename and
        blob 
        """
        for blob in blobs:
            name = Helper.get_name(blob.name)
            if name == blob_to_search:
                filename = Helper.get_file_name(blob.name)
                return (filename, blob)
        return (None, None)

    def get_random_blob(self, prefix: str, delimiter: str = None):
        """ 
        Gets all blobs in a directory and randomly pick one to retrieve. 
        Returns the blob and its filename. If there are no files, 
        return None.

        This can be useful for cases such as playing randomly-chosen audio 
        clips, or retrieving randomly-chosen images.
        """
        audio_blobs = self.get_blobs(prefix=prefix, delimiter=delimiter,
                                     return_as_list=True)
        if len(audio_blobs) == 0 or all(blob is None for blob in audio_blobs):
            return None
        while True:
            random_blob = choice(audio_blobs)
            random_blob_name = random_blob.name
            random_blob_file_ext = Helper.get_file_extension(random_blob_name)
            if random_blob_file_ext:
                random_blob_name = Helper.get_file_name(random_blob_name)
                return (random_blob, random_blob_name)

    def get_signed_url_for_blob(self, blob: Blob, expiration_time_in_mins: int = 15) -> str:
        """
        Generates v4 signed URL for downloading a blob. 
        Source: 
        https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers#storage-signed-url-object-python

        NOTE: Not sure if this is needed though... but, I'll leave it 
        here for now. Could be useful in the near future.
        """
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_time_in_mins),
            method="GET",
        )
        return url
