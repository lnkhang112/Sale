#Odoo BOPIS Module – Buy Online, Pick Up In Store

Module này mở rộng quy trình bán hàng của Odoo, bổ sung tính năng **BOPIS** cho Website, Sale Order và Stock Picking.  
Khách hàng đặt hàng online – đến cửa hàng nhận – nhân viên scan QR để xác nhận lấy hàng.

##Tính năng nổi bật

###Hiển thị lựa chọn BOPIS trên Website
- Khách hàng có thể chọn **"Nhận hàng tại cửa hàng"** ở bước checkout.
- Lưu thông tin lựa chọn vào `sale.order`.

###Tự động tạo Stock Picking dạng BOPIS
- Khi đơn hàng xác nhận, hệ thống sinh ra `stock.picking` với type tương ứng.
- Tracking đầy đủ trạng thái chuẩn Odoo.

###Sinh QR Code tự động
- QR được tạo ngay khi đơn hàng hoàn tất.
- QR xuất hiện trên:
  - Trang xác nhận đơn hàng (confirmation page)
  - Email gửi khách hàng
  - Form view trong backend
