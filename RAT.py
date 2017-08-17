
# -*- coding: utf-8 -*-

#coding=utf-8
import os
import re
import sys
import pytest
import logging
import unittest
import subprocess
import time

from appium import webdriver

import config

from lib.syshelper import SysHelper
from lib.sociushelper import SociusHelper
from lib.accounthelper import AccountHelper

# Returns abs path relative to this file and not cwd
PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)

path1 = "../SociusAppium/test_resources/."

# logger
logger = logging.getLogger()
logFormatter = logging.Formatter(
    '[%(asctime)-15s][%(filename)s][%(funcName)s#%(lineno)d] %(message)s')
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logFormatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)


def getDeviceProp(prop):
    p1 = subprocess.Popen(['adb', 'shell', 'getprop'], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', prop], stdin=p1.stdout, stdout=subprocess.PIPE)
        
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    line = p2.communicate()[0]
    # parse value
    p = re.compile('\[ro.{}\]: \[(.+)\]'.format(prop))
    return p.findall(line)[0]


#putout testfile
def nofile():
    subprocess.Popen(['adb', 'shell', 'rm', '/sdcard/Soocii/*.mp4', '/sdcard/soocii/*.jpeg'])

#putin testfile
def havefile():
    subprocess.Popen(['adb', 'push', os.path.abspath(path1)+"/.", '/sdcard/Soocii/'])


class BaseTests(unittest.TestCase):
    def setUp(self):
        desired_caps = {}
        desired_caps['platformName'] = 'Android'
        desired_caps['platformVersion'] = getDeviceProp('build.version.release')
        desired_caps['deviceName'] = 'Android Emulator'
        desired_caps['unicodeKeyboard'] = True
        desired_caps['resetKeyboard'] = True
        #desired_caps['full-reset'] = True
        desired_caps['app'] = PATH(
            config.PATH_TO_TEST_APK
        )
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.driver.implicitly_wait(5)
        self.logger = logging.getLogger()

        self.syshelper = SysHelper(self.driver, desired_caps['platformName'], desired_caps['platformVersion'])
        self.sociushelper = SociusHelper(self.driver, desired_caps['platformName'], desired_caps['platformVersion'])

    def tearDown(self):
        # TODO: reset keyboard

        # remove app
        self.driver.close_app()

        # end the session
        self.driver.quit()

        


class FacebookAccountTests(BaseTests):
    # Login with existing facebook account and enable usage access once
    @pytest.mark.first
    def test_fresh_install_and_enable_usage_access(self):
        try:
            expectedDisplayName=config.EXISTING_FACEBOOK_ACCOUNT1_DISPLAYNAME
            expectedSoociiId=config.EXISTING_FACEBOOK_ACCOUNT1_SOOCIIID

            # Facebook Login button on Soocii
            self.sociushelper.click_facebook_login_button()
            self.syshelper.login_facebook_account(config.EXISTING_FACEBOOK_ACCOUNT1, config.EXISTING_FACEBOOK_ACCOUNT1_PWD)

            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()

            # only need to skip floating ball guide mark once
            self.sociushelper.skip_floating_ball_guide_mark()

            # only need to enable usage access once
            self.syshelper.enable_usage_access()

            # only need to enable draw on top layer once
            self.syshelper.enable_draw_on_top_layer()

            # expect seeing discover page
            self.assertTrue(self.sociushelper.is_discover())
            displayName, soociiId = self.sociushelper.get_personal_info()
            self.assertTrue(expectedDisplayName==displayName,
                u"expect value {}, but return unexpected {}".format(expectedDisplayName, displayName))
            self.assertTrue(expectedSoociiId==soociiId,
                u"expect value {}, but return unexpected {}".format(expectedSoociiId, soociiId))

            # switch to home and back to soocii
            self.syshelper.press_home_key()
            self.syshelper.start_soocii()
            displayName, soociiId = self.sociushelper.get_personal_info()
            self.assertTrue(expectedDisplayName==displayName,
                u"expect value {}, but return unexpected {}".format(expectedDisplayName, displayName))
            self.assertTrue(expectedSoociiId==soociiId,
                u"expect value {}, but return unexpected {}".format(expectedSoociiId, soociiId))
            # don't delete the account
        except:
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_fresh_install_and_enable_usage_access")
            raise

    # Login with new facebook account who friend with existing facebook/soocii account
    def test_login_new_facebook_account(self):
        try:
            expectedDisplayName=config.NEW_FACEBOOK_ACCOUNT1_DISPLAYNAME
            expectedSoociiId=config.NEW_FACEBOOK_ACCOUNT1_SOOCIIID

            # Facebook Login button on Soocii
            self.sociushelper.click_facebook_login_button()
            self.syshelper.login_facebook_account(config.NEW_FACEBOOK_ACCOUNT1, config.NEW_FACEBOOK_ACCOUNT1_PWD)

            # flow to create new account
            self.sociushelper.create_account(expectedDisplayName, expectedSoociiId)
            self.sociushelper.add_followers()

            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()

            # expect seeing discover page
            self.assertTrue(self.sociushelper.is_discover())
            displayName, soociiId = self.sociushelper.get_personal_info()
            self.assertTrue(expectedDisplayName==displayName,
                u"expect value {}, but return unexpected {}".format(expectedDisplayName, displayName))
            self.assertTrue(expectedSoociiId==soociiId,
                u"expect value {}, but return unexpected {}".format(expectedSoociiId, soociiId))

            # switch to home and back to soocii
            self.syshelper.press_home_key()
            self.syshelper.start_soocii()
            displayName, soociiId = self.sociushelper.get_personal_info()
            self.assertTrue(expectedDisplayName==displayName,
                u"expect value {}, but return unexpected {}".format(expectedDisplayName, displayName))
            self.assertTrue(expectedSoociiId==soociiId,
                u"expect value {}, but return unexpected {}".format(expectedSoociiId, soociiId))
        except:
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_login_new_facebook_account")
            raise
        finally:
            # delete the account for next time
            self.sociushelper.click_delete_account_button()

    # TODO: Login with new facebook account who does NOT friend with any facebook/soocii account

class EmailAccountTests(BaseTests):
    # Login with new email account
    def test_login_new_email_account(self):
        try:
            accounthelper = AccountHelper()

            # Create new account button on Soocii
            self.sociushelper.click_create_new_account_using_email_button()

            # flow to create new account
            self.sociushelper.create_account(
                accounthelper.name,
                accounthelper.name,
                accounthelper.email,
                "password1234")

            # confirm to follow recommended celebrity
            self.sociushelper.click_confirm_recommended_celebrity()

            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()

            # expect seeing discover page
            self.assertTrue(self.sociushelper.is_discover())
            displayName, soociiId = self.sociushelper.get_personal_info()
            self.assertTrue(accounthelper.name==displayName,
                            u"expect value {}, but return unexpected {}".format(accounthelper.name, displayName))
            self.assertTrue(accounthelper.name==soociiId,
                            u"expect value {}, but return unexpected {}".format(accounthelper.name, soociiId))

            # switch to home and back to soocii
            self.syshelper.press_home_key()
            self.syshelper.start_soocii()
            displayName, soociiId = self.sociushelper.get_personal_info()
            self.assertTrue(accounthelper.name==displayName,
                            u"expect value {}, but return unexpected {}".format(accounthelper.name, displayName))
            self.assertTrue(accounthelper.name==soociiId,
                            u"expect value {}, but return unexpected {}".format(accounthelper.name, soociiId))
        except:
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_login_new_email_account")
            raise
        finally:
            # delete the account for next time
            self.sociushelper.click_delete_account_button()

    # Login with existing email account
    def test_login_existing_email_account(self):
        try:
            accounthelper = AccountHelper()

            # Create new account button on Soocii
            self.sociushelper.click_create_new_account_using_email_button()

            # flow to create new account
            self.sociushelper.create_account(
                accounthelper.name,
                accounthelper.name,
                accounthelper.email,
                "password1234")

            # confirm to follow recommended celebrity
            self.sociushelper.click_confirm_recommended_celebrity()

            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()

            # expect seeing discover page
            self.assertTrue(self.sociushelper.is_discover())

            # logout
            self.sociushelper.click_logout_button()

            # login with the same account again
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account(accounthelper.email, "password1234")

            # expect seeing discover page
            self.assertTrue(self.sociushelper.is_discover())
            displayName, soociiId = self.sociushelper.get_personal_info()
            self.assertTrue(accounthelper.name==displayName,
                            u"expect value {}, but return unexpected {}".format(accounthelper.name, displayName))
            self.assertTrue(accounthelper.name==soociiId,
                            u"expect value {}, but return unexpected {}".format(accounthelper.name, soociiId))

            # switch to home and back to soocii
            self.syshelper.press_home_key()
            self.syshelper.start_soocii()
            displayName, soociiId = self.sociushelper.get_personal_info()
            self.assertTrue(accounthelper.name==displayName,
                            u"expect value {}, but return unexpected {}".format(accounthelper.name, displayName))
            self.assertTrue(accounthelper.name==soociiId,
                            u"expect value {}, but return unexpected {}".format(accounthelper.name, soociiId))
        except:
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_login_existing_email_account")
            raise
        finally:
            # delete the account for next time
            self.sociushelper.click_delete_account_button()

    # TODO: create existing email account

class DiscoveryAndSupportTests(BaseTests):
    """docstring for DiscoveryAndSupportTests"""
    def test_allpage(self):
        try:
            expectedDisplayName=config.EXISTING_FACEBOOK_ACCOUNT1_DISPLAYNAME
            expectedSoociiId=config.EXISTING_FACEBOOK_ACCOUNT1_SOOCIIID

            # Facebook Login button on Soocii
            self.sociushelper.click_facebook_login_button()
            self.syshelper.login_facebook_account(config.EXISTING_FACEBOOK_ACCOUNT1, config.EXISTING_FACEBOOK_ACCOUNT1_PWD)

            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()

            self.sociushelper.swipe_discover()

            # check newsfeedinfo
            self.assertTrue(self.sociushelper.get_newsfeed_info())

            #check aboutme
            self.assertTrue(self.sociushelper.check_aboutme(expectedDisplayName))

            #check support
            self.assertTrue(self.sociushelper.check_support())

            #check friendlist
            self.assertTrue(self.sociushelper.get_friendlist_info())

            self.sociushelper.swipe_to_fans()

            self.assertTrue(self.sociushelper.check_suggest())

            self.sociushelper.swipe_to_SearchId()
            self.sociushelper.get_idsearch("scheng1")
            self.sociushelper.go_back()
            self.sociushelper.swipe_discover()
            self.sociushelper.swipe_refresh()
        except:
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_allpage")
            raise

    def test_discoverytap(self):
        reload(sys)
        sys.setdefaultencoding('utf-8')
        try:
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")
                
            self.sociushelper.click_require_permission_button()

            self.sociushelper.swipe_discover()

            for x in range(10):
                self.sociushelper.swipe_loading()
                self.assertTrue(self.sociushelper.get_videocard())

            for y in range(15):
                self.sociushelper.swipe_refresh()

            self.sociushelper.click_onlinevideocard()

            self.sociushelper.click_videocard()

            self.sociushelper.swipe_refresh()
            self.sociushelper.swipe_refresh()

            self.sociushelper.check_hashtag()


        except Exception as e:
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_discoverytap")
            raise

    def test_zendesk(self):
        try:
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")
                
            self.sociushelper.click_require_permission_button()



            self.sociushelper.swipe_to_support()

            self.sociushelper.check_zendesk()

            self.sociushelper.check_faq()

            self.sociushelper.check_contact("ignore this ! automation test!")
        except Exception as e:
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_zendesk")
            raise

class LiveTests(BaseTests):
    def test_open_live(self):
        try:
            # #login_with_email
            # self.sociushelper.click_login_by_email_link()
            # self.sociushelper.login_account("channing@gmail.com", "zxasqw123")

            # self.sociushelper.click_require_permission_button()

            expectedDisplayName=config.EXISTING_FACEBOOK_ACCOUNT1_DISPLAYNAME
            expectedSoociiId=config.EXISTING_FACEBOOK_ACCOUNT1_SOOCIIID

            # Facebook Login button on Soocii
            self.sociushelper.click_facebook_login_button()
            self.syshelper.login_facebook_account(config.EXISTING_FACEBOOK_ACCOUNT1, config.EXISTING_FACEBOOK_ACCOUNT1_PWD)

            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()

            #open_streaming 10 times
            # for x in range(10):
            self.sociushelper.click_open_fab_button()
            self.sociushelper.choice_game()
            self.sociushelper.setting_live()
            self.sociushelper.click_camera_floatball()
            self.sociushelper.broadcast("hi welcome to my broadcast")
            for y in range(3):
                self.sociushelper.change_camera()
            #share post
            self.sociushelper.stop_live()
            self.sociushelper.go_to_post()
            self.sociushelper.share_live_record("broadcast",x)
            self.sociushelper.click_camera_floatball()
            self.sociushelper.back_soocii()
            self.sociushelper.swipe_to_aboutme()
            self.sociushelper.refresh_aboutme()

        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_open_live")
            raise
    def test_download(self):
        try:
            #login_with_email
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")

            self.sociushelper.click_require_permission_button()
            #open_streaming 10 times
            for x in range(10):
                self.sociushelper.click_open_fab_button()
                self.sociushelper.choice_game()
                self.sociushelper.setting_live()
                self.sociushelper.click_camera_floatball()
                self.sociushelper.stop_live()
                self.sociushelper.go_to_post()
                #download live record and edit
                self.sociushelper.download_live_record()
                self.sociushelper.edit_live_record()
                self.sociushelper.edit_next()
                #get time
                localtime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                self.sociushelper.share_live_record(localtime+"download",x)
                self.syshelper.start_snake_off()
                self.sociushelper.click_camera_floatball()
                self.sociushelper.back_soocii()
                self.sociushelper.swipe_to_aboutme()
                self.sociushelper.refresh_aboutme()


        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_download")
            raise

    def test_viewer(self):
        try:
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")
            self.sociushelper.click_require_permission_button()
            for x in range(10):
                #go to live in discover

                self.sociushelper.gotochat_with_discovery()
                #viewer test
                self.sociushelper.chat_live("i love this game")
                self.sociushelper.click_sharelink_button()
                self.sociushelper.click_viewer_button()
                self.assertTrue(self.sociushelper.check_viewer_name())
                self.sociushelper.click_viewer_button()
                self.sociushelper.leave_live()

        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_viewer")
            raise

class PostsTests(BaseTests):
    def test_edit_posts(self):
        havefile()
        try:

            expectedDisplayName=config.EXISTING_FACEBOOK_ACCOUNT1_DISPLAYNAME
            expectedSoociiId=config.EXISTING_FACEBOOK_ACCOUNT1_SOOCIIID

            # Facebook Login button on Soocii
            self.sociushelper.click_facebook_login_button()
            self.syshelper.login_facebook_account(config.EXISTING_FACEBOOK_ACCOUNT1, config.EXISTING_FACEBOOK_ACCOUNT1_PWD)

            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()


            self.sociushelper.swipe_to_aboutme()

            self.sociushelper.click_viedo_to_share()##click viedo button in about me,and share viedo

            self.sociushelper.check_and_refresh_share_posts("video from about me")


            self.sociushelper.check_post()

        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_edit_post")
            raise

    def test_firstposts(self):
        try:
            nofile()
            accounthelper = AccountHelper()

            # Create new account button on Soocii
            self.sociushelper.click_create_new_account_using_email_button()

            # flow to create new account
            self.sociushelper.create_account(
                accounthelper.name,
                accounthelper.name,
                accounthelper.email,
                "password1234")

            # confirm to follow recommended celebrity
            self.sociushelper.click_confirm_recommended_celebrity()

            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()


            self.sociushelper.swipe_to_aboutme()

            self.sociushelper.new_local_video_post()



        except:
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_firstposts")
            raise

    def test_comments(self):
        try:
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")

            self.sociushelper.click_require_permission_button()

            self.sociushelper.swipe_to_aboutme()
            self.sociushelper.swipe_posts()#into  single posts
            check_a = self.sociushelper.check_like_num(["like", u"個棒"]) # (a) to get like of number
            self.sociushelper.swipe_like()#click like
            check_b = self.sociushelper.check_like_num(["like", u"個棒"]) # (b) to get like of number
            self.assertTrue(check_b > check_a) #After click like_bt , compare (a) with (b) count whether +1

            self.sociushelper.swipe_like()#click like ,let like = 0
            self.sociushelper.swipe_and_send_message("this is qa message")#input message to share_EditText ,and click send button 

            self.assertTrue(self.sociushelper.is_message())#if message visibility
            self.syshelper.press_back_key()
        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_comments")
            raise
        finally:
            pass

    def test_share_posts(self):
        try:
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")
            self.sociushelper.click_require_permission_button()

            self.sociushelper.swipe_to_aboutme()
            self.sociushelper.swipe_posts()#click share button
            self.sociushelper.swpie_share_posts()#click share posts button
            self.sociushelper.swipe_share_posts_to_soocii()

            self.sociushelper.input_send_share_message("this is share post testing")#input message and click send button

            self.sociushelper.swipe_refresh()

            self.assertTrue(self.sociushelper.chech_share_posts())#make sure


        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_share_posts")
            raise
        finally:
            pass


    def test_upload_picture(self):
        try:

            nofile()#delete all file
            accounthelper = AccountHelper()

            # Create new account button on Soocii
            self.sociushelper.click_create_new_account_using_email_button()

            # flow to create new account
            self.sociushelper.create_account(
                accounthelper.name,
                accounthelper.name,
                accounthelper.email,
                "password1234")

            # confirm to follow recommended celebrity
            self.sociushelper.click_confirm_recommended_celebrity()
            self.sociushelper.click_require_permission_button()


            self.sociushelper.swipe_to_aboutme()

            self.sociushelper.click_share_picture()#click image button in about me,and share photo 

            self.sociushelper.check_and_refresh_share_posts("upload img from local")
            #come back to aboutme,to check share posts is exist (picture)

        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_upload_picture")
            raise
        finally:
            pass

    def test_check_and_share_record(self):
        
        try:
            nofile()#clear all file
            
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")
            self.sociushelper.click_require_permission_button()
            havefile()#put file to test case (photo and viedo)
            self.sociushelper.waitii()
            
            
            self.sociushelper.swipe_to_aboutme()

            self.sociushelper.click_viedo_to_share()##click viedo button in about me,and share viedo

            self.sociushelper.check_and_refresh_share_posts("video from about me")
            #come back to aboutme,to check share posts is exist (viedo)

        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_check_and_share_record")
            raise
        finally:
            pass
    def test_share_posts_to_otherapp(self):
        try:
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")
                
            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()

            self.sociushelper.swipe_to_aboutme()

            self.assertTrue(self.sociushelper.check_share_otherapp_posts())
        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_share_posts_to_otherapp")
            raise

class otherposts(BaseTests):
    def test_posts_like_comment_share(self):
        try:
            self.sociushelper.click_login_by_email_link()
            self.sociushelper.login_account("channing@gmail.com", "zxasqw123")
                
            # confirm acquiring permission dialog
            self.sociushelper.click_require_permission_button()

            self.sociushelper.swipe_discover()
            self.sociushelper.swipe_to_friendlist()
            self.sociushelper.swipe_to_SearchId()
            self.sociushelper.get_idsearch("scheng1")
            self.sociushelper.swipe_fans_list_photo_image_view()
            check_c = self.sociushelper.check_like_num(["shares",u"個分享"]) # (a) to get share of number
            self.sociushelper.swipe_posts()
            self.sociushelper.click_single_viedo()
            self.assertTrue(self.sociushelper.check_single_posts())

          

            check_a = self.sociushelper.check_like_num(["like", u"個棒"]) # (a) to get like of number
            self.sociushelper.swipe_like()#click like
            self.sociushelper.edit_cover()
            check_b = self.sociushelper.check_like_num(["like", u"個棒"]) # (b) to get like of number

            self.assertTrue(check_b > check_a) #After click like_bt , compare (a) with (b) count whether +1
            self.sociushelper.swipe_like()#click like ,let like = 0
            

            self.sociushelper.click_comment()
            self.sociushelper.swipe_and_send_message("this is msg testing")
            self.assertTrue(self.sociushelper.is_posts_message("this is msg testing"))
            self.sociushelper.go_back()
            
            self.sociushelper.edit_cover()
            self.sociushelper.edit_cover()

            self.sociushelper.swpie_share_posts()
            self.sociushelper.swipe_share_posts_to_soocii()
            self.sociushelper.input_send_share_message("share post testing")#input message and click send button
            

            check_d = self.sociushelper.check_like_num(["shares",u"個分享"]) # (a) to get share of number
            self.assertTrue(check_d > check_c) #After click like_bt , compare (a) with (b) count whether +1

            self.sociushelper.go_back()




        except :
            self.logger.info('caught exception: {}'.format(sys.exc_info()[0]))
            self.syshelper.capture_screen("test_posts_like_comment_share")
            raise

        