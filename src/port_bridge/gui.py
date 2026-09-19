"""PySide6 GUI for PortBridge."""
import threading
from datetime import datetime
from PySide6.QtCore import QSettings,QTimer,QObject,Signal
from PySide6.QtWidgets import QApplication,QComboBox,QFormLayout,QGroupBox,QHBoxLayout,QLabel,QLineEdit,QMainWindow,QMessageBox,QPushButton,QSpinBox,QStackedWidget,QTextEdit,QVBoxLayout,QWidget
from .core import TcpBridgeConfig,TcpBridgeServer,VisaBridgeConfig,VisaBridgeServer,list_visa_resources,test_tcp_endpoint,test_visa_endpoint

class Signals(QObject):
    log=Signal(str); tested=Signal(bool,str); scanned=Signal(object,str)

class PortBridgeWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle("PortBridge");self.resize(900,680)
        self.settings=QSettings("PortBridge","PortBridge");self.signals=Signals();self.bridge=None
        self.signals.log.connect(self.log);self.signals.tested.connect(self.test_done);self.signals.scanned.connect(self.scan_done)
        root=QWidget();lay=QVBoxLayout(root);lay.addWidget(QLabel("<h2>PortBridge</h2>"))
        common=QGroupBox("Bridge configuration");f=QFormLayout(common)
        self.mode=QComboBox();self.mode.addItems(["Network / TCP","USB / VISA"]);f.addRow("Mode",self.mode)
        self.host=QLineEdit("0.0.0.0");f.addRow("Listen address",self.host)
        self.port=QSpinBox();self.port.setRange(1,65535);self.port.setValue(15025);f.addRow("Listen port",self.port)
        self.timeout=QSpinBox();self.timeout.setRange(100,120000);self.timeout.setValue(5000);self.timeout.setSuffix(" ms");f.addRow("Timeout",self.timeout);lay.addWidget(common)
        self.stack=QStackedWidget();n=QGroupBox("TCP target");nf=QFormLayout(n);self.remote=QLineEdit("192.168.1.100");self.rport=QSpinBox();self.rport.setRange(1,65535);self.rport.setValue(5025);nf.addRow("Host",self.remote);nf.addRow("Port",self.rport);self.stack.addWidget(n)
        v=QGroupBox("VISA target");vf=QFormLayout(v);row=QHBoxLayout();self.resource=QComboBox();self.resource.setEditable(True);self.scan=QPushButton("Scan VISA");self.scan.clicked.connect(self.scan_visa);row.addWidget(self.resource);row.addWidget(self.scan);vf.addRow("Resource",row);self.backend=QLineEdit();vf.addRow("Backend",self.backend);self.stack.addWidget(v);lay.addWidget(self.stack)
        self.mode.currentIndexChanged.connect(self.mode_changed)
        a=QHBoxLayout();self.test=QPushButton("Test (*IDN?)");self.start=QPushButton("Start");self.stop=QPushButton("Stop");self.stop.setEnabled(False);self.test.clicked.connect(self.test_connection);self.start.clicked.connect(self.start_bridge);self.stop.clicked.connect(self.stop_bridge);a.addWidget(self.test);a.addWidget(self.start);a.addWidget(self.stop);a.addStretch();lay.addLayout(a)
        self.status=QLabel("Stopped");self.client=QLabel("-");self.traffic=QLabel("RX 0 B / TX 0 B");sf=QFormLayout();sf.addRow("Status",self.status);sf.addRow("Client",self.client);sf.addRow("Traffic",self.traffic);lay.addLayout(sf)
        self.logs=QTextEdit();self.logs.setReadOnly(True);lay.addWidget(self.logs,1);self.setCentralWidget(root)
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(500)
    def mode_changed(self,i):self.stack.setCurrentIndex(i);self.port.setValue(15025 if i==0 else 15026)
    def log(self,m):self.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {m}")
    def scan_visa(self):
        self.scan.setEnabled(False)
        def w():
            try:self.signals.scanned.emit(list_visa_resources(self.backend.text().strip() or None),"")
            except Exception as e:self.signals.scanned.emit([],str(e))
        threading.Thread(target=w,daemon=True).start()
    def scan_done(self,items,error):
        self.scan.setEnabled(True)
        if error:QMessageBox.warning(self,"VISA",error);return
        self.resource.clear();self.resource.addItems([str(x) for x in items]);self.log(f"Found {len(items)} VISA resources")
    def test_connection(self):
        self.test.setEnabled(False);mode=self.mode.currentIndex()
        def w():
            try:
                if mode==0:r=test_tcp_endpoint(self.remote.text().strip(),self.rport.value(),self.timeout.value()/1000)
                else:r=test_visa_endpoint(self.resource.currentText().strip(),self.timeout.value(),self.backend.text().strip() or None)
                self.signals.tested.emit(True,r or "Connected")
            except Exception as e:self.signals.tested.emit(False,str(e))
        threading.Thread(target=w,daemon=True).start()
    def test_done(self,ok,text):
        self.test.setEnabled(True);self.log(text);(QMessageBox.information if ok else QMessageBox.warning)(self,"Connection test",text)
    def start_bridge(self):
        try:
            if self.mode.currentIndex()==0:b=TcpBridgeServer(TcpBridgeConfig(self.host.text().strip(),self.port.value(),self.remote.text().strip(),self.rport.value(),self.timeout.value()/1000),on_event=self.signals.log.emit)
            else:b=VisaBridgeServer(VisaBridgeConfig(self.resource.currentText().strip(),self.host.text().strip(),self.port.value(),self.timeout.value(),backend=self.backend.text().strip() or None),on_event=self.signals.log.emit)
            b.start();self.bridge=b;self.start.setEnabled(False);self.stop.setEnabled(True);self.mode.setEnabled(False);self.status.setText("Running")
        except Exception as e:QMessageBox.critical(self,"Start failed",str(e))
    def stop_bridge(self):
        if self.bridge:self.bridge.stop();self.bridge=None
        self.start.setEnabled(True);self.stop.setEnabled(False);self.mode.setEnabled(True);self.status.setText("Stopped");self.client.setText("-")
    def refresh(self):
        if not self.bridge:return
        s=self.bridge.snapshot();self.client.setText(s.client_address or "Waiting");self.traffic.setText(f"RX {s.bytes_from_client} B / TX {s.bytes_to_client} B")
    def closeEvent(self,e):self.stop_bridge();super().closeEvent(e)

def run_gui():
    app=QApplication.instance() or QApplication([]);w=PortBridgeWindow();w.show();return app.exec()
