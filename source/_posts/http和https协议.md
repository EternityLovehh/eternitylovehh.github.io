---
title: http和https协议
date: 2021-02-21 19:03:41
tags: 网络
---

### get和post的区别

1. 请求方式，get使用url+？拼接字符串进行请求，post通过request body上传请求
2. 提交数据大小，get提交数据限制最大为1024个字节，post理论上没有大小限制
3. 对参数的数据类型，get只接受ASCII字符，post没有限制
4. 缓存，get请求能被浏览器缓存，post不能缓存，刷新页面的时候数据会重新提交

### cookie和session区别

1. cookie 是以文本的形式保存在客户端的，session是存储在服务端的
2. 有效期不同，cookie可以设置很长的时间，session在服务器上保存一定时间就会消失
3. 安全性上，cookie存在本地有被拦截的风险
4. 对服务器造成的压力不同，每个用户都会产生session，当并发量大的时候，服务器压力比较大

### tcp 三次握手

建立tcp连接，需要客户端和服务端总共发送3个包 确认连接的建立

![](https://img-blog.csdn.net/20180719110828114?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3hpYW9taW5nMTAwMDAx/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70)

1. 客户端发数据包给服务器，并进入SENT状态，等待服务器确认
2. 服务器收到客户端请求后，反馈给客户端确认信息ACK，同时发送SYN包
3. 客户端收到服务端返回的数据ACK+SYN后，向服务器发送ACK表示确认收到，完成tcp的连接

### tcp 四次挥手断开连接

![](https://img-blog.csdn.net/20180719110841774?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3hpYW9taW5nMTAwMDAx/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70)

1. 客户端发送一个FIN，用来关闭客户端到服务器数据传输，客户端进去wait状态
2. 服务器收到FIN后，发送一个ACK给客户端，确认收到，服务器进入CLOSE_WAIT状态
3. 服务器发送一个FIN，用来关闭服务器到客户端的数据传输，服务器进入LAST_ACK状态
4. 客户端收到FIN后，客户端进入TIME_WAIT状态，并发送一个ACK给服务器，服务器收到并进入CLOSE状态

### 为什么建立连接是三次握手，而关闭连接却是四次挥手呢？

建立连接的时候，服务器在listen状态下，收到建立连接的请求报文后，把ACK和SYN放在一个报文里发送给客户端。

关闭连接的时候，服务器收到对方的FIN报文时，仅仅表示对方不在发送数据了，但还能接收，且服务器也未必全部数据都成功发送给客户端了，因此先发送ACK告知客户端，收到断开连接的请求了，这样客户端就不会因为没有收到应答 继续发送断开连接的请求了，服务器在处理完数据后，主动发送FIN报文给客户端表示同意现在关闭连接，这样可以保证数据通信正常可靠的完成。

### http的工作流程

http是基于TCP/IP协议的一种传输协议

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

#### 加密算法

对称加密，加密和解密用的秘钥是一样的DES，AES

非对称加密，公钥加密，私钥解密，公钥可以公开给别人进行加密，私钥存放在服务端不公开，RSA

### HTTPS协议

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

### HTTP 与 HTTPS 区别

1. http是明文传输，数据都是未加密的，https数据传输过程是加密的，安全性好
2. https协议需要申请CA数字证书
3. http页面响应速度比https快，https除了tcp/ip层要进行握手，ssl层也要握手进行加密解密
4. http的端口是80，https端口是443
5. https是http+ssl/tls，所以https比http更耗费服务器资源