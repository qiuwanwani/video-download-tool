<template>
  <div class="min-h-screen bg-black text-gray-100 font-['Open_Sans']">
    <!-- 导航栏 -->
    <nav class="bg-[#0F0F23] bg-opacity-95 backdrop-blur-sm fixed top-4 left-4 right-4 z-50 rounded-xl shadow-lg transition-all duration-300">
      <div class="max-w-7xl mx-auto px-6 py-4">
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-gradient-to-r from-[#E11D48] to-[#7E22CE] flex items-center justify-center shadow-lg">
              <span class="text-white font-bold text-xl font-['Poppins']">VD</span>
            </div>
            <span class="text-xl font-bold text-white font-['Poppins']">视频下载工具</span>
          </div>
          <div class="hidden md:flex items-center space-x-8">
            <a href="#" class="text-gray-300 hover:text-white transition-colors font-medium">首页</a>
            <a href="#" class="text-gray-300 hover:text-white transition-colors font-medium">使用教程</a>
            <a href="#" class="text-gray-300 hover:text-white transition-colors font-medium">支持的平台</a>
            <a href="#" class="text-gray-300 hover:text-white transition-colors font-medium">关于我们</a>
            <button class="px-6 py-3 bg-[#E11D48] hover:bg-[#be123c] text-white rounded-lg font-medium transition-all transform hover:scale-105 shadow-lg flex items-center gap-2">
              <CrownIcon class="w-5 h-5" />
              升级VIP
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主要内容 -->
    <main class="max-w-7xl mx-auto px-6 pt-32 pb-20">
      <!-- 英雄区域 -->
      <section class="text-center mb-20 animate-fade-in">
        <h1 class="text-6xl font-bold mb-6 text-white font-['Poppins']">
          视频下载工具
        </h1>
        <p class="text-xl text-gray-300 max-w-3xl mx-auto mb-10">
          支持1800+网站的视频下载，简单易用，一键下载
        </p>
        <div class="inline-block mb-12">
          <div class="px-4 py-2 bg-[#1E1B4B] rounded-full text-sm text-gray-300 shadow-lg flex items-center gap-2">
            <FireIcon class="w-4 h-4 text-orange-500" />
            支持YouTube、B站、TikTok等1800+平台
          </div>
        </div>
        <!-- 设备展示 -->
        <div class="max-w-3xl mx-auto">
          <div class="bg-[#0F0F23] rounded-3xl p-8 shadow-2xl border border-gray-800">
            <div class="aspect-video bg-gray-900 rounded-xl overflow-hidden">
              <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=video%20download%20tool%20interface%20modern%20dark%20theme&image_size=landscape_16_9" alt="视频下载工具界面" class="w-full h-full object-cover" />
            </div>
          </div>
        </div>
      </section>

      <!-- 下载区域 -->
      <section class="bg-[#0F0F23] rounded-2xl shadow-2xl p-10 mb-20 transform transition-all duration-300 hover:shadow-3xl border border-gray-800">
        <h2 class="text-3xl font-bold mb-10 text-center text-white font-['Poppins']">视频下载</h2>
        
        <!-- URL输入表单 -->
        <form @submit.prevent="parseVideo" class="mb-10">
          <div class="flex flex-col md:flex-row gap-4">
            <input
              v-model="videoUrl"
              type="url"
              placeholder="请输入视频URL"
              class="flex-1 px-6 py-4 rounded-xl bg-gray-900 border border-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-[#E11D48] transition-all"
              required
            />
            <button
              type="submit"
              class="px-8 py-4 bg-[#E11D48] hover:bg-[#be123c] text-white font-medium rounded-xl transition-all transform hover:scale-105 shadow-lg"
            >
              解析视频
            </button>
          </div>
          <p v-if="error" class="mt-4 text-[#E11D48] text-sm animate-fade-in">
            {{ error }}
          </p>
        </form>

        <!-- 视频信息和质量选择 -->
        <div v-if="videoInfo" class="mb-10 animate-slide-up">
          <div class="mb-8">
            <div class="flex flex-col md:flex-row gap-8">
              <div class="md:w-2/5">
                <!-- 视频封面 -->
                <div 
                  class="rounded-xl overflow-hidden shadow-lg transform transition-all duration-300 hover:scale-105 border border-gray-700 cursor-pointer relative group"
                  @click="playVideo"
                >
                  <img 
                    :src="getProxyImageUrl(videoInfo.thumbnail)" 
                    :alt="videoInfo.title" 
                    class="w-full h-auto object-cover transition-opacity duration-300 group-hover:opacity-70"
                  />
                  <div class="absolute inset-0 flex items-center justify-center bg-gradient-to-t from-black/70 to-transparent group-hover:from-black/80 transition-all duration-300">
                    <div class="transform transition-all duration-300 group-hover:scale-110">
                      <PlayIcon />
                    </div>
                  </div>
                </div>
                
                <!-- 视频标题 -->
                <h3 class="text-2xl font-bold mt-6 mb-4 text-white font-['Poppins']">{{ videoInfo.title }}</h3>
                
                <!-- 视频描述 -->
                <div v-if="videoInfo.description" class="mb-6">
                  <h4 class="font-medium mb-3 text-gray-300">视频介绍:</h4>
                  <div class="bg-gray-900/50 rounded-lg p-4 border border-gray-800">
                    <p class="text-gray-400 whitespace-pre-line">{{ videoInfo.description }}</p>
                  </div>
                </div>
                
                <!-- 视频详情信息 -->
                <div class="mt-6">
                  <h4 class="font-medium mb-3 text-gray-300">视频详情:</h4>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <p class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">时长:</span>
                      {{ formatDuration(videoInfo.duration) }}
                    </p>
                    <p class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">来源:</span>
                      {{ getVideoSource(videoUrl) }}
                    </p>
                    <p class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">格式数:</span>
                      {{ videoInfo.formats.length }}
                    </p>
                    <p v-if="videoInfo.subtitles && videoInfo.subtitles.length > 0" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">字幕:</span>
                      {{ videoInfo.subtitles.length }} 个
                    </p>
                    <p v-if="videoInfo.uploader" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">上传者:</span>
                      {{ videoInfo.uploader }}
                    </p>
                    <p v-if="videoInfo.upload_date" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">上传日期:</span>
                      {{ formatDate(videoInfo.upload_date) }}
                    </p>
                    <p v-if="videoInfo.view_count" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">观看次数:</span>
                      {{ formatNumber(videoInfo.view_count) }}
                    </p>
                    <p v-if="videoInfo.like_count" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">点赞次数:</span>
                      {{ formatNumber(videoInfo.like_count) }}
                    </p>
                  </div>
                </div>
              </div>
              <div class="md:w-3/5">
                <h4 class="font-medium mb-4 text-gray-300">选择格式:</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
                  <div
                    v-for="format in videoInfo.formats"
                    :key="format.format_id"
                    class="border border-gray-700 rounded-lg p-4 cursor-pointer hover:bg-gray-900 transition-all transform hover:scale-[1.02]"
                    :class="{
                      'border-[#E11D48] bg-gray-800 shadow-lg shadow-[#E11D48]/20 ring-2 ring-[#E11D48]/30': selectedFormat === format.format_id
                    }"
                    @click="selectedFormat = format.format_id"
                  >
                    <div class="flex justify-between items-center">
                      <span class="font-medium text-white">{{ format.resolution }}</span>
                      <span class="text-sm text-gray-400">{{ format.ext }}</span>
                    </div>
                    <div v-if="format.filesize" class="text-sm text-gray-400 mt-2">
                      {{ formatFilesize(format.filesize) }}
                    </div>
                  </div>
                </div>

                <button
                  @click="downloadVideo"
                  class="w-full py-4 bg-[#E11D48] hover:bg-[#be123c] text-white font-medium rounded-xl transition-all transform hover:scale-[1.02] shadow-lg"
                  :disabled="!selectedFormat"
                >
                  下载视频
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 视频播放模态框 -->
        <div v-if="isPlaying" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80">
          <div class="bg-[#0F0F23] rounded-xl shadow-2xl p-6 max-w-4xl w-full mx-4">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-xl font-bold text-white font-['Poppins']">视频播放</h3>
              <button @click="closeVideoPlayer" class="text-gray-400 hover:text-white transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div class="aspect-video bg-black rounded-lg overflow-hidden">
              <video :src="videoPlayerUrl" controls autoplay class="w-full h-full object-contain"></video>
            </div>
          </div>
        </div>

        <!-- 下载进度 -->
        <div v-if="downloadProgress > 0" class="mb-10 animate-fade-in">
          <div class="flex justify-between mb-3">
            <span class="font-medium text-gray-300">下载进度:</span>
            <span class="font-medium text-white">{{ Math.round(downloadProgress) }}%</span>
          </div>
          <div class="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
            <div
              class="bg-gradient-to-r from-[#E11D48] to-[#7E22CE] h-full rounded-full transition-all duration-300 ease-out"
              :style="{ width: downloadProgress + '%' }"
            ></div>
          </div>
        </div>
      </section>

      <!-- 下载历史 -->
      <section class="bg-[#0F0F23] rounded-2xl shadow-2xl p-10 mb-20 transform transition-all duration-300 hover:shadow-3xl border border-gray-800">
        <div class="flex justify-between items-center mb-10">
          <h2 class="text-3xl font-bold text-white font-['Poppins']">下载历史</h2>
          <button
            @click="clearHistory"
            class="text-sm text-[#E11D48] hover:text-[#f43f5e] transition-colors transform hover:scale-105 font-medium"
          >
            清空历史
          </button>
        </div>
        <div v-if="downloadHistory.length === 0" class="text-center py-16 text-gray-400">
          <div class="flex justify-center mb-6">
            <DownloadIcon class="w-16 h-16 text-gray-600" />
          </div>
          <p class="text-lg">暂无下载历史</p>
        </div>
        <div v-else class="space-y-4">
          <div
            v-for="(item, index) in downloadHistory"
            :key="index"
            class="border border-gray-700 rounded-lg p-5 transition-all duration-300 hover:shadow-md transform hover:translate-y-[-2px] hover:bg-gray-900/50"
          >
            <div class="flex justify-between items-start">
              <div>
                <h3 class="font-medium text-white">{{ item.title }}</h3>
                <p class="text-sm text-gray-400 mt-1">{{ item.timestamp }}</p>
              </div>
              <a
                :href="item.direct_link"
                target="_blank"
                class="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors text-sm font-medium"
              >
                重新下载
              </a>
            </div>
          </div>
        </div>
      </section>

      <!-- VIP付费引导 -->
      <section class="bg-gradient-to-r from-[#1E1B4B] to-[#0F0F23] rounded-2xl shadow-2xl p-12 mb-20 transform transition-all duration-300 hover:shadow-3xl border border-gray-800">
        <div class="max-w-3xl mx-auto text-center">
          <h2 class="text-4xl font-bold mb-6 text-white font-['Poppins']">升级到VIP</h2>
          <p class="mb-8 text-lg text-gray-300">
            享受无限制下载、高速下载、批量下载等高级功能
          </p>
          <button class="px-12 py-4 bg-[#E11D48] hover:bg-[#be123c] text-white font-bold rounded-xl hover:shadow-lg transition-all transform hover:scale-105 shadow-lg mb-10">
            立即升级
          </button>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            <div class="bg-gray-900/50 backdrop-blur-sm rounded-lg p-5 border border-gray-800">
              <div class="mb-4">
                <ZapIcon class="w-8 h-8 text-yellow-500" />
              </div>
              <h3 class="font-bold mb-3 text-white font-['Poppins']">高速下载</h3>
              <p class="text-sm text-gray-400">享受更快的下载速度，节省时间</p>
            </div>
            <div class="bg-gray-900/50 backdrop-blur-sm rounded-lg p-5 border border-gray-800">
              <div class="mb-4">
                <DownloadIcon class="w-8 h-8 text-blue-500" />
              </div>
              <h3 class="font-bold mb-3 text-white font-['Poppins']">批量下载</h3>
              <p class="text-sm text-gray-400">一次下载多个视频，提高效率</p>
            </div>
            <div class="bg-gray-900/50 backdrop-blur-sm rounded-lg p-5 border border-gray-800">
              <div class="mb-4">
                <ShieldIcon class="w-8 h-8 text-green-500" />
              </div>
              <h3 class="font-bold mb-3 text-white font-['Poppins']">无限制</h3>
              <p class="text-sm text-gray-400">无下载次数限制，想下多少就下多少</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 支持的平台 -->
      <section class="mb-20">
        <h2 class="text-3xl font-bold mb-10 text-center text-white font-['Poppins']">支持的平台</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <VideoIcon class="w-12 h-12 text-red-500" />
            </div>
            <p class="font-medium text-white">YouTube</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <ZapIcon class="w-12 h-12 text-cyan-500" />
            </div>
            <p class="font-medium text-white">TikTok</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <VideoIcon class="w-12 h-12 text-pink-500" />
            </div>
            <p class="font-medium text-white">B站</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <HeartIcon class="w-12 h-12 text-purple-500" />
            </div>
            <p class="font-medium text-white">Instagram</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <LinkIcon class="w-12 h-12 text-blue-500" />
            </div>
            <p class="font-medium text-white">Twitter</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <MoreIcon class="w-12 h-12 text-blue-400" />
            </div>
            <p class="font-medium text-white">1800+ 更多</p>
          </div>
        </div>
      </section>

      <!-- 常见问题 -->
      <section class="bg-[#0F0F23] rounded-2xl shadow-2xl p-10 mb-20 border border-gray-800">
        <h2 class="text-3xl font-bold mb-10 text-center text-white font-['Poppins']">常见问题</h2>
        <div class="space-y-4">
          <div class="border border-gray-700 rounded-lg overflow-hidden">
            <button class="w-full px-6 py-4 text-left font-medium flex justify-between items-center hover:bg-gray-900/50 transition-colors text-white">
              <span>如何下载视频？</span>
              <ArrowDownIcon class="w-5 h-5 text-gray-400" />
            </button>
            <div class="px-6 py-4 bg-gray-900/30">
              <p class="text-gray-400">
                只需在输入框中粘贴视频URL，点击解析视频，选择想要的格式，然后点击下载视频按钮即可。
              </p>
            </div>
          </div>
          <div class="border border-gray-700 rounded-lg overflow-hidden">
            <button class="w-full px-6 py-4 text-left font-medium flex justify-between items-center hover:bg-gray-900/50 transition-colors text-white">
              <span>支持哪些网站？</span>
              <ArrowDownIcon class="w-5 h-5 text-gray-400" />
            </button>
            <div class="px-6 py-4 bg-gray-900/30">
              <p class="text-gray-400">
                支持YouTube、B站、TikTok、Instagram、Twitter等1800+网站的视频下载。
              </p>
            </div>
          </div>
          <div class="border border-gray-700 rounded-lg overflow-hidden">
            <button class="w-full px-6 py-4 text-left font-medium flex justify-between items-center hover:bg-gray-900/50 transition-colors text-white">
              <span>下载速度为什么很慢？</span>
              <ArrowDownIcon class="w-5 h-5 text-gray-400" />
            </button>
            <div class="px-6 py-4 bg-gray-900/30">
              <p class="text-gray-400">
                下载速度受网络环境和视频源服务器影响。升级到VIP可以获得更快的下载速度。
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 页脚 -->
    <footer class="bg-[#0F0F23] py-16 border-t border-gray-800">
      <div class="max-w-7xl mx-auto px-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          <div>
            <h3 class="text-lg font-bold mb-6 text-white font-['Poppins']">视频下载工具</h3>
            <p class="text-gray-400 text-sm">
              支持1800+网站的视频下载，简单易用，一键下载
            </p>
          </div>
          <div>
            <h3 class="text-lg font-bold mb-6 text-white font-['Poppins']">快速链接</h3>
            <ul class="space-y-3 text-sm">
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">首页</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">使用教程</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">支持的平台</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">关于我们</a></li>
            </ul>
          </div>
          <div>
            <h3 class="text-lg font-bold mb-6 text-white font-['Poppins']">法律</h3>
            <ul class="space-y-3 text-sm">
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">隐私政策</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">使用条款</a></li>
              <li><a href="#" class="text-gray-400 hover:text-white transition-colors">版权声明</a></li>
            </ul>
          </div>
          <div>
            <h3 class="text-lg font-bold mb-6 text-white font-['Poppins']">联系我们</h3>
            <ul class="space-y-3 text-sm">
              <li class="text-gray-400">邮箱：contact@example.com</li>
              <li class="text-gray-400">微信：video-download-tool</li>
            </ul>
          </div>
        </div>
        <div class="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
          <div class="mb-4 md:mb-0">
            <p class="text-gray-400 text-sm">
              © 2026 视频下载工具. 保留所有权利.
            </p>
          </div>
          <div class="flex space-x-6">
            <a href="#" class="text-gray-400 hover:text-white transition-colors">
              <VideoIcon class="w-6 h-6" />
            </a>
            <a href="#" class="text-gray-400 hover:text-white transition-colors">
              <LinkIcon class="w-6 h-6" />
            </a>
            <a href="#" class="text-gray-400 hover:text-white transition-colors">
              <DownloadIcon class="w-6 h-6" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios';
import { FireIcon, VideoIcon, DownloadIcon, LinkIcon, CrownIcon, ShieldIcon, ZapIcon, HeartIcon, ArrowDownIcon, MoreIcon, PlayIcon } from './icons'

export default {
  name: 'App',
  components: {
    FireIcon,
    VideoIcon,
    DownloadIcon,
    LinkIcon,
    CrownIcon,
    ShieldIcon,
    ZapIcon,
    HeartIcon,
    ArrowDownIcon,
    MoreIcon,
    PlayIcon
  },
  data() {
    return {
      videoUrl: '',
      videoInfo: null,
      selectedFormat: '',
      error: '',
      downloadProgress: 0,
      downloadHistory: JSON.parse(localStorage.getItem('downloadHistory') || '[]'),
      isPlaying: false,
      videoPlayerUrl: ''
    };
  },
  methods: {
    async parseVideo() {
      try {
        this.error = '';
        this.videoInfo = null;
        this.selectedFormat = '';
        
        const response = await axios.get('http://localhost:8000/api/parse', {
          params: { url: this.videoUrl }
        });
        
        this.videoInfo = response.data;
      } catch (error) {
        this.error = error.response?.data?.detail || '解析失败，请检查URL是否正确';
      }
    },
    async downloadVideo() {
      if (!this.selectedFormat) return;
      
      try {
        this.error = '';
        this.downloadProgress = 0;
        
        const response = await axios.get('http://localhost:8000/api/download', {
          params: {
            url: this.videoUrl,
            format_id: this.selectedFormat
          }
        });
        
        // 模拟下载进度
        let progress = 0;
        const interval = setInterval(() => {
          progress += 5;
          this.downloadProgress = progress;
          if (progress >= 100) {
            clearInterval(interval);
            // 保存到下载历史
            this.saveToHistory(response.data);
          }
        }, 200);
        
        // 打开下载链接
        window.open(response.data.direct_link, '_blank');
      } catch (error) {
        this.error = error.response?.data?.detail || '下载失败，请稍后重试';
      }
    },
    saveToHistory(videoData) {
      const historyItem = {
        title: videoData.title,
        direct_link: videoData.direct_link,
        timestamp: new Date().toLocaleString()
      };
      
      this.downloadHistory.unshift(historyItem);
      // 只保留最近10条记录
      if (this.downloadHistory.length > 10) {
        this.downloadHistory = this.downloadHistory.slice(0, 10);
      }
      
      localStorage.setItem('downloadHistory', JSON.stringify(this.downloadHistory));
    },
    clearHistory() {
      this.downloadHistory = [];
      localStorage.removeItem('downloadHistory');
    },
    formatDuration(seconds) {
      if (!seconds) return '未知';
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = Math.floor(seconds % 60);
      
      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
      }
    },
    formatFilesize(bytes) {
      if (!bytes) return '未知';
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;
      
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }
      
      return `${size.toFixed(2)} ${units[unitIndex]}`;
    },
    getProxyImageUrl(url) {
      if (!url) return '';
      // 使用后端代理接口处理跨域图片
      return `http://localhost:8000/api/proxy-image?url=${encodeURIComponent(url)}`;
    },
    getVideoSource(url) {
      if (!url) return '未知';
      
      const platforms = {
        'youtube.com': 'YouTube',
        'bilibili.com': 'B站',
        'tiktok.com': 'TikTok',
        'instagram.com': 'Instagram',
        'twitter.com': 'Twitter',
        'facebook.com': 'Facebook',
        'twitter.com': 'Twitter',
        'reddit.com': 'Reddit',
        'vimeo.com': 'Vimeo',
        'dailymotion.com': 'Dailymotion'
      };
      
      for (const [domain, name] of Object.entries(platforms)) {
        if (url.includes(domain)) {
          return name;
        }
      }
      
      return '其他平台';
    },
    formatDate(dateStr) {
      if (!dateStr) return '未知';
      // 处理YYYYMMDD格式的日期
      if (dateStr.length === 8) {
        const year = dateStr.substring(0, 4);
        const month = dateStr.substring(4, 6);
        const day = dateStr.substring(6, 8);
        return `${year}-${month}-${day}`;
      }
      return dateStr;
    },
    formatNumber(num) {
      if (!num) return '未知';
      // 格式化数字，添加千位分隔符
      return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    playVideo() {
      // 简单的视频播放实现
      // 实际项目中可能需要使用更复杂的视频播放器
      if (this.videoInfo && this.videoInfo.formats && this.videoInfo.formats.length > 0) {
        // 选择第一个格式作为播放源
        const firstFormat = this.videoInfo.formats[0];
        // 构建播放URL
        this.videoPlayerUrl = `http://localhost:8000/api/get-direct-link?url=${encodeURIComponent(this.videoUrl)}&format_id=${firstFormat.format_id}`;
        this.isPlaying = true;
      }
    },
    closeVideoPlayer() {
      this.isPlaying = false;
      this.videoPlayerUrl = '';
    }
  }
};
</script>

<style scoped>
/* 组件样式 */
.animate-fade-in {
  animation: fadeIn 0.6s ease-in-out;
}

.animate-slide-up {
  animation: slideUp 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
