#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a simple utility to fetch content of code reviews."""
import os
import json
import urllib2
import sys
import subprocess
import tempfile


def DownloadPatchSet(cl_number):
  """Returns the name of the patch file for a given CL.

  Args:
    cl_number: The CL number for the code review.

  Returns:
    The name fo the patch file, or a None if unable to download
    the patch.
  """
  try:
    test_cl = int(cl_number)
    if cl_number != str(test_cl):
      return
  except ValueError:
    return

  url = 'https://codereview.appspot.com/api/{0}/'.format(cl_number)
  url_object = urllib2.urlopen(url)

  if url_object.code != 200:
    return

  data = url_object.read()

  try:
    data_obj = json.loads(data)
  except ValueError:
    return

  patches = data_obj.get('patchsets', [])
  last_patch = patches.pop()

  patch_url = 'https://codereview.appspot.com/download/issue{}_{}.diff'.format(
      cl_number, last_patch)

  patch_object = urllib2.urlopen(patch_url)
  if patch_object.code != 200:
    return

  patch_data = patch_object.read()
  patch_file_name = ''
  with tempfile.NamedTemporaryFile(delete=False) as patch_file_object:
    patch_file_object.write(patch_data)
    patch_file_name = patch_file_object.name

  return patch_file_name


if __name__ == '__main__':
  if len(sys.argv) != 2:
    print 'Need to provide a CL number.'
    sys.exit(1)

  code_review_number = sys.argv[1]
  patch_file = DownloadPatchSet(code_review_number)

  if not patch_file:
    print 'Unable to download a patch set, exiting.'
    sys.exit(1)

  branch_name = 'review_{}'.format(code_review_number)
  branch_exit = os.system('git checkout -b {}'.format(branch_name))
  if branch_exit:
    print 'Unable to create a new branch, exiting.'
    sys.exit(1)

  patch_exit = os.system('patch -p1 < {}'.format(patch_file))
  if patch_exit:
    print 'Unable to patch files.'
    sys.exit(1)

  git_add = subprocess.Popen(
      'git status -s', shell=True, stdout=subprocess.PIPE)
  git_to_add = []
  for git_line in git_add.stdout:
    if git_line.startswith('??'):
      git_to_add.append(git_line[3:-1])

  print git_to_add
  for file_to_add in git_to_add:
    os.system('git add {}'.format(git_to_add))

  print 'Files added to git branch'
  os.system('git commit -a "Committing CL to branch"')

  os.remove(patch_file)

  print 'Patch downloaded and applied, branch {} created.'.format(
      branch_name)
  print 'Remember to delete branch when done testing/inspecting.'
  print 'git checkout master && git branch -D {}'.format(branch_name)

