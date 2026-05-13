---
title: 网络请求http和https
date: 2019-05-07 15:18:02
categories:
  - android
tags:
  - 安卓学习记录
---
http是基于TCP/IP协议的一种传输协议  
tcp 三次握手：  
客户端发数据给服务器  
服务器收到数据反馈到客户端表示收到  
客户端收到服务端返回的数据，发送确认收到

tcp 四次挥手断开连接  
在客户端给服务端发送了断开请求后， 客户端还可以继续给服务端发送请求，但服务端不再给客户端发送消息

socket 套接字是对Tcp/Ip协议的封装

http的工作流程  
第一步：地址解析，从url中解析协议名称，主机名，端口号和对应的页面地址。  
第二步：封装http的请求数据包：这一步主要是封装自己的信息，比如在post请求时，我们会塞进一个data数据。  
第三步：封装tcp包，建立连接：因为是基于tcp的协议，网络连接是tcp来完成的，必然要封装成tcp包，然后tcp再做自己工作，比如封装ip包，一层层往下传。  
第四步：发送请求：数据整好了，连接也完事了，那就发送action了。  
第五步：服务端响应：接受到请求，然后给出响应。  
第六步:服务端关闭tcp的连接：一次通信完成之后，若conection的设置不是keep-live的话，服务端会自动关闭tcp的连接。

```
 /**
     * http内部socket实现
     */
    public void testHttp(){
        try {
            URL url = new URL("http://www.baidu.com");
            StringBuffer stringBuffer = new StringBuffer();
            //请求行
            stringBuffer.append("GET  ");
            stringBuffer.append(url.getFile());
            stringBuffer.append(" ");
            stringBuffer.append("HTTP/1.1");
            stringBuffer.append("\r\n");
            //请求头
            stringBuffer.append("Host: ");
            stringBuffer.append(url.getHost());
            stringBuffer.append("\r\n");
            //空行
            stringBuffer.append("\r\n");

            final Socket socket = new Socket();
            //dns解析，将host解析为ip
            socket.connect(new InetSocketAddress(url.getHost(), url.getPort()));

            //读取http响应
            final BufferedReader br = new BufferedReader(new
                    InputStreamReader(
                    socket.getInputStream(),"utf-8"));
            BufferedWriter bf = new BufferedWriter((new OutputStreamWriter(
                    socket.getOutputStream())));
            new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                     String line = null;  
        			 while((line = br.readLine())!= null)  {  
          				  System.out.println(line);  
       				 }  
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }).start();

            bf.write(stringBuffer.toString());
            bf.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
```

HTTPS协议 = HTTP协议 + SSL/TLS协议，除了tcp/ip层要进行握手，ssl层也要进行握手进行加密解密。https同时使用了对称加密和非对称加密，对称加密的过程需要客户端的一个密钥，为了确保能把该密钥安全的传输到服务器端，采用非对称加密对该密钥进行加密传输。

SSL的全称是Secure Sockets Layer，即安全套接层协议，是为网络通信提供安全及  
数据完整性的一种安全协议。

TLS的全称是Transport Layer Security，即安全传输层协议，最新版TLS（Transport Layer Security，传输层安全协议）是IETF（Internet Engineering Task Force，Internet工程任务组）制定的一种新的协议，它建立在SSL 3.0协议规范之上，是SSL 3.0的后续版本。在TLS与SSL3.0之间存在着显著的差别，主要是它们所支持的加密算法不同，所以TLS与SSL3.0不能互操作。虽然TLS与SSL3.0在加密算法上不同，但是在我们理解HTTPS的过程中，我们可以把SSL和TLS看做是同一个协议。

https需要证书，使用系统默认信任的证书  
如果是没有信任证书的请求，需要信任自定义的证书

```
 public void testHttps(){
        try {
            URL url = new URL("http://www.baidu.com");
            StringBuffer stringBuffer = new StringBuffer();
            //请求行
            stringBuffer.append("GET  ");
            stringBuffer.append(url.getFile());
            stringBuffer.append(" ");
            stringBuffer.append("HTTP/1.1");
            stringBuffer.append("\r\n");
            //请求头
            stringBuffer.append("Host: ");
            stringBuffer.append(url.getHost());
            stringBuffer.append("\r\n");
            //空行
            stringBuffer.append("\r\n");
            //这里可以是：SSL、TLS
            SSLContext context = SSLContext.getInstance("SSL");
            Socket socket = (SSLSocketFactory.getDefault()).createSocket(url.getHost(), url.getPort());
            //读取http响应
            final BufferedReader br = new BufferedReader(new
                    InputStreamReader(
                    socket.getInputStream(),"utf-8"));
            BufferedWriter bf = new BufferedWriter((new OutputStreamWriter(
                    socket.getOutputStream())));
            new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        br.readLine();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }).start();

            bf.write(stringBuffer.toString());
            bf.flush();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
    }
```

okhttp 需要设置hostnameVerferiy()方法验证域名，是为了防止中间人攻击（拦截网络通信，对数据进行篡改）
