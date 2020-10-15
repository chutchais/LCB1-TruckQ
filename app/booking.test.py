import unittest
from booking import app
from booking import making_booking_test_data,making_bl_test_data
import json

# GET method
class ExportWithContainerTestCase(unittest.TestCase):
    """Test of Export with Container (GET)"""
    booking = 'BOOK1'#'0237SDJ'
    container = 'TEST0000000'#'SKHU9533067'

    def setUp(self):
        making_booking_test_data(self.booking,self.container)

#     def test_booking_0_initial_data(self):
#         making_booking_test_data(self.booking,self.container)

    def test_booking_1_inquiry(self):
            url = f'/api/booking/{self.booking}/{self.container}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['booking'] == self.booking)
            self.assertTrue(response.json['container'] == self.container)
            self.assertTrue(response.json['result'] == "ACCEPT")
    
    def test_booking_2_sucess_reserve(self):
            url = f'/api/booking/{self.booking}/{self.container}/reserve'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['booking'] == self.booking)
            self.assertTrue(response.json['container'] == self.container)
            self.assertTrue(response.json['result'] == "ok")# dict(success=True))

    def test_booking_3_failed_reserve(self):
            url = f'/api/booking/{self.booking}/{self.container}/reserve'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['booking'] == self.booking)
            self.assertTrue(response.json['container'] == self.container)
            self.assertTrue(response.json['result'] == "failed")# dict(success=True))
    
    def test_booking_4_cancel(self):
        url = f'/api/booking/{self.booking}/{self.container}/cancel'
        tester = app.test_client(self)
        response = tester.get(url, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['booking'] == self.booking)
        self.assertTrue(response.json['container'] == self.container)
        self.assertTrue(response.json['result'] == "ok")# dict(success=True))

# POST Method
class ExportWithContainerPostTestCase(unittest.TestCase):
    booking = 'BOOK1'#'0237SDJ'
    container = 'TEST0000000'#'SKHU9533067'

    def setUp(self):
        making_booking_test_data(self.booking,self.container)
#     def test_booking_post_0_initial_data(self):
#         making_booking_test_data(self.booking,self.container)

    def test_booking_post_1_check_success(self):
        url = f'/api/booking'
        tester = app.test_client(self)
        payload ={'booking':self.booking,
                'container':self.container,
                'action':'CHECK'
                }
        response = tester.post(url,json=payload,follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['booking'] == self.booking)
        self.assertTrue(response.json['container'] == self.container)
        self.assertTrue(response.json['result'] == "ACCEPT")
        
    def test_booking_post_2_check_notaccept1(self):
        url = f'/api/booking'
        tester = app.test_client(self)
        payload ={'booking':'ABC',
                'container':self.container,
                'action':'CHECK'
                }
        response = tester.post(url,json=payload,follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['booking'] == 'ABC')
        self.assertTrue(response.json['container'] == self.container)
        self.assertTrue(response.json['result'] == "NOTACCEPT")

    def test_booking_post_3_check_notaccept2(self):
        url = f'/api/booking'
        tester = app.test_client(self)
        payload ={'booking':self.booking,
                'container':'XYZ',
                'action':'CHECK'
                }
        response = tester.post(url,json=payload,follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['booking'] == self.booking)
        self.assertTrue(response.json['container'] == 'XYZ')
        self.assertTrue(response.json['result'] == "NOTACCEPT")
    
    def test_booking_post_4_reserve_success(self):
        url = f'/api/booking'
        tester = app.test_client(self)
        payload ={'booking':self.booking,
                'container':self.container,
                'action':'RESERVE'
                }
        response = tester.post(url,json=payload,follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['booking'] == self.booking)
        self.assertTrue(response.json['container'] == self.container)
        self.assertTrue(response.json['result'] == "ok")

    def test_booking_post_5_reserve_fail(self):
        url = f'/api/booking'
        tester = app.test_client(self)
        payload ={'booking':self.booking,
                'container':self.container,
                'action':'RESERVE'
                }
        response = tester.post(url,json=payload,follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['booking'] == self.booking)
        self.assertTrue(response.json['container'] == self.container)
        self.assertTrue(response.json['result'] == "failed")

    def test_booking_post_6_cancel_success(self):
        url = f'/api/booking'
        tester = app.test_client(self)
        payload ={'booking':self.booking,
                'container':self.container,
                'action':'CANCEL'
                }
        response = tester.post(url,json=payload,follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['booking'] == self.booking)
        self.assertTrue(response.json['container'] == self.container)
        self.assertTrue(response.json['result'] == "ok")

# GET Method
class ImportWithContainerTestCase(unittest.TestCase):
    bl = 'BL1'#'0237SDJ'
    container = 'TEST0000000'#'SKHU9533067'

    def setUp(self):
        making_bl_test_data(self.bl,self.container)

#     def test_bl_get_container_0_initial_data(self):
#         making_bl_test_data(self.bl,self.container)

    def test_bl_get_container_1_inquiry(self):
            bl = self.bl
            container = self.container
            url = f'/api/bl/{bl}/{container}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "ACCEPT")
    def test_bl_get_container_2_reserve_success(self):
            bl = self.bl
            container = self.container
            url = f'/api/bl/{bl}/{container}/reserve'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "ok")
    def test_bl_get_container_3_reserve_failed(self):
            bl = self.bl
            container = self.container
            url = f'/api/bl/{bl}/{container}/reserve'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "failed")
    def test_bl_get_container_4_cancel(self):
            bl = self.bl
            container = self.container
            url = f'/api/bl/{bl}/{container}/cancel'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "ok")

# POST Method
class ImportWithContainerPostTestCase(unittest.TestCase):
    bl = 'BL1'#'0237SDJ'
    container = 'TEST0000000'#'SKHU9533067'

    def setUp(self):
        making_bl_test_data(self.bl,self.container)

#     def test_bl_post_container_0_initial_data(self):
#         making_bl_test_data(self.bl,self.container)

    def test_bl_post_container_1_check(self):
            bl = self.bl
            container = self.container
            url = f'/api/bl/container'
            tester = app.test_client(self)
            payload ={'bl':self.bl,
                'container':self.container,
                'action':'CHECK'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['container'] == self.container)
            self.assertTrue(response.json['result'] == "ACCEPT")

    def test_bl_post_container_2_reserve_success(self):
            bl = self.bl
            container = self.container
            url = f'/api/bl/container'
            tester = app.test_client(self)
            payload ={'bl':self.bl,
                'container':self.container,
                'action':'RESERVE'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['container'] == self.container)
            self.assertTrue(response.json['result'] == "ok")

    def test_bl_post_container_3_reserve_failed(self):
            bl = self.bl
            container = self.container
            url = f'/api/bl/container'
            tester = app.test_client(self)
            payload ={'bl':self.bl,
                'container':self.container,
                'action':'RESERVE'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['container'] == self.container)
            self.assertTrue(response.json['result'] == "failed")

    def test_bl_post_container_4_cancel(self):
            bl = self.bl
            container = self.container
            url = f'/api/bl/container'
            tester = app.test_client(self)
            payload ={'bl':self.bl,
                'container':self.container,
                'action':'CANCEL'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['container'] == self.container)
            self.assertTrue(response.json['result'] == "ok")

# GET Method
class ImportLeamchabangTestCase(unittest.TestCase):
    bl = 'BL2'#'0237SDJ'
    container = 'TEST0000001'#'SKHU9533067'

    def setUp(self):
        making_bl_test_data(self.bl,self.container)

#     def test_bl_LCB_0_initial_data(self):
#         making_bl_test_data(self.bl,self.container)

    def test_bl_LCB_1_check_success(self):
            bl = self.bl
            qty = 1
            url = f'/api/bl/{bl}/check/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['result'] == "ACCEPT")
    def test_bl_LCB_2_check_fail(self):
            bl = self.bl
            qty = 100
            url = f'/api/bl/{bl}/check/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "NOTACCEPT")
    def test_bl_LCB_3_reserve(self):
            bl = self.bl
            qty = 1
            url = f'/api/bl/{bl}/reserve/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "ok")
    def test_bl_LCB_4_reserve_over_qty(self):
            bl = self.bl
            qty = 100
            url = f'/api/bl/{bl}/reserve/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "failed")

# POST Method
class ImportLeamchabangPostTestCase(unittest.TestCase):
    bl = 'BL1'#'0237SDJ'
    container = 'TEST0000000'#'SKHU9533067'

    def setUp(self):
        making_bl_test_data(self.bl,self.container)

#     def test_bl_post_LCB_0_initial_data(self):
#         making_bl_test_data(self.bl,self.container)

    def test_bl_post_LCB_1_check(self):
            bl = self.bl
            qty = "1"
            url = f'/api/bl/qty'
            tester = app.test_client(self)
            payload ={'bl':self.bl,
                'qty':qty,
                'action':'CHECK'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['qty'] == qty)
            self.assertTrue(response.json['result'] == "ACCEPT")

    def test_bl_post_LCB_2_reserve_success(self):
            bl = self.bl
            qty = "1"
            url = f'/api/bl/qty'
            tester = app.test_client(self)
            payload ={'bl':self.bl,
                'qty':qty,
                'action':'RESERVE'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['qty'] == qty)
            self.assertTrue(response.json['result'] == "ok")

    def test_bl_post_LCB_3_reserve_failed(self):
            bl = self.bl
            qty = "100"
            url = f'/api/bl/qty'
            tester = app.test_client(self)
            payload ={'bl':self.bl,
                'qty':qty,
                'action':'RESERVE'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['result'] == "failed")

    def test_bl_post_LCB_4_cancel(self):
            bl = self.bl
            qty = "1"
            url = f'/api/bl/qty'
            tester = app.test_client(self)
            payload ={'bl':self.bl,
                'qty':qty,
                'action':'CANCEL'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['bl'] == self.bl)
            self.assertTrue(response.json['qty'] == qty)
            self.assertTrue(response.json['result'] == "ok")

# Get
class ImportLadkrabangTestCase(unittest.TestCase):
    shore = 'SHORE1'#'0237SDJ'
    container = 'SHOR0000000'#'SKHU9533067'

    def setUp(self):
        making_booking_test_data(self.shore,self.container)

#     def test_shore_LKB_0_initial_data(self):
#         making_booking_test_data(self.shore,self.container)

    def test_shore_LKB_1_check_success(self):
            shore = self.shore
            qty = 1
            url = f'/api/shore/{shore}/check/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "ACCEPT")
    def test_shore_LKB_2_check_fail(self):
            shore = self.shore
            qty = 100
            url = f'/api/shore/{shore}/check/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "NOTACCEPT")
    def test_shore_LKB_3_reserve(self):
            shore = self.shore
            qty = 1
            url = f'/api/shore/{shore}/reserve/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "ok")
    def test_shore_LKB_4_reserve_over_qty(self):
            shore = self.shore
            qty = 100
            url = f'/api/shore/{shore}/reserve/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "failed")
    def test_shore_LKB_5_cancel_qty(self):
            shore = self.shore
            qty = 1
            url = f'/api/shore/{shore}/cancel/{qty}'
            tester = app.test_client(self)
            response = tester.get(url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['result'] == "ok")

# Post
class ImportLadkrabangPostTestCase(unittest.TestCase):
    shore = 'SHORE1'#'0237SDJ'
    container = 'SHOR0000000'#'SKHU9533067'

    def setUp(self):
        making_booking_test_data(self.shore,self.container)

#     def test_shore_post_LKB_0_initial_data(self):
#         making_booking_test_data(self.shore,self.container)

    def test_shore_post_LKB_1_check_success(self):
            shore = self.shore
            qty = 1
            url = f'/api/shore/qty'
            tester = app.test_client(self)
            payload ={'shore':self.shore,
                'qty':qty,
                'action':'CHECK'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['shore'] == self.shore)
            self.assertTrue(response.json['result'] == "ACCEPT")

    def test_shore_post_LKB_2_check_failed(self):
            shore = self.shore
            qty = 100
            url = f'/api/shore/qty'
            tester = app.test_client(self)
            payload ={'shore':self.shore,
                'qty':qty,
                'action':'CHECK'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['shore'] == self.shore)
            self.assertTrue(response.json['result'] == "NOTACCEPT")

    def test_shore_post_LKB_3_reserve_success(self):
            shore = self.shore
            qty = 1
            url = f'/api/shore/qty'
            tester = app.test_client(self)
            payload ={'shore':self.shore,
                'qty':qty,
                'action':'RESERVE'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['shore'] == self.shore)
            self.assertTrue(response.json['result'] == "ok")

    def test_shore_post_LKB_4_reserve_failed(self):
            shore = self.shore
            qty = 100
            url = f'/api/shore/qty'
            tester = app.test_client(self)
            payload ={'shore':self.shore,
                'qty':qty,
                'action':'RESERVE'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['shore'] == self.shore)
            self.assertTrue(response.json['result'] == "failed")

    def test_shore_post_LKB_5_cancel(self):
            shore = self.shore
            qty = 1
            url = f'/api/shore/qty'
            tester = app.test_client(self)
            payload ={'shore':self.shore,
                'qty':qty,
                'action':'CANCEL'
                }
            response = tester.post(url,json=payload,follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['shore'] == self.shore)
            self.assertTrue(response.json['result'] == "ok")

if __name__ == '__main__':
    unittest.main()