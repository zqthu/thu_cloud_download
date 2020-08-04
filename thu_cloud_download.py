# coding=utf-8
import requests
import json
import os
import re

"""
MIT License

Copyright (c) 2020 zqthu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

class THUCloud():
    def __init__(self, shared_link, outdir=None):
        self.headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"}
        
        if "/f/" in shared_link: # single file
            self.is_dir = False
            archive = shared_link.split("/f/")[-1].split("/")[0]
            self.api_link = "https://cloud.tsinghua.edu.cn/f/{}/".format(archive)
            self.file_link = "https://cloud.tsinghua.edu.cn/f/{}/?dl=1".format(archive)
        elif '/d/' in shared_link: # dir
            self.is_dir = True
            archive = shared_link.split("/d/")[-1].split("/")[0]
            self.api_link = "https://cloud.tsinghua.edu.cn/api/v2.1/share-links/{}/dirents/".format(archive)
            self.file_link = "https://cloud.tsinghua.edu.cn/d/{}/files/".format(archive)
        else:
            raise ValueError("Cannot parse the shared link.")

        if outdir is None:
            self.current_dir = os.getcwd()
        else:
            self.current_dir = os.path.abspath(outdir)
        if not os.path.exists(self.current_dir):
            os.mkdir(self.current_dir)   
        
    def _move_to(self, to_dir):
        self.current_dir = os.path.abspath(os.path.join(self.current_dir, to_dir))
        # print(self.current_dir)
        if not os.path.exists(self.current_dir):
            os.mkdir(self.current_dir)        

    def _parse_url(self, path):
        url = self.api_link + '?path=' + path
        response = requests.get(url=url, headers=self.headers)
        assert response.status_code == 200
        return response.content.decode()

    def _retrieve_file(self, url, name): # for small files
        file_path = os.path.join(self.current_dir, name)
        response = requests.get(url=url, headers=self.headers)
        assert response.status_code == 200
        content = response.content
        with open(file_path, "wb") as f:
            f.write(content)

    def _recursion_download(self, path):
        response = self._parse_url(path)
        response_dict = json.loads(response)
        for item in response_dict['dirent_list']:
            # print(item)
            if item['is_dir'] == True:
                next_path = item['folder_path']
                self._move_to(item['folder_name'])
                self._recursion_download(next_path)
            else:
                url = self.file_link + '?p=' + item['file_path'] + '&dl=1'
                self._retrieve_file(url, item['file_name'])
        self._move_to("..")
    
    def download(self):
        if self.is_dir:
            self._recursion_download("/") # initial data, default download all files
            # TODO: support download list, block list and regex pattern
        else:
            response = requests.get(url=self.api_link, headers=self.headers)
            assert response.status_code == 200
            content = response.content.decode()
            name = re.search(r"fileName: '(.*)',", content).group(1)
            self._retrieve_file(self.file_link, name)

if __name__ == "__main__":
    """
    Examples of shared link:
        https://cloud.tsinghua.edu.cn/f/2c50c14239b641d09632/
        https://cloud.tsinghua.edu.cn/d/36320b3f8a86487c931a/
    """

    # replace the shared_link here
    shared_link = "https://cloud.tsinghua.edu.cn/f/2c50c14239b641d09632/"

    # output dir (optional)
    out_dir = "archive"

    t = THUCloud(shared_link, out_dir)
    t.download()