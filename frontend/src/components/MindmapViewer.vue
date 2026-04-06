<template>
  <div class="mindmap-wrapper" ref="wrapperRef">
    <div v-if="!markdown" class="text-center text-gray-500 py-20">
      暂无思维导图内容
    </div>
    <div v-else class="mindmap-container">
      <!-- 工具栏 -->
      <div class="mindmap-toolbar">
        <button @click="toggleFullscreen" class="toolbar-btn" :class="isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'" title="全屏">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
          </svg>
        </button>
        <button @click="downloadSVG" class="toolbar-btn" :class="isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'" title="下载SVG">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
        </button>
      </div>
      <svg ref="svgRef" class="mindmap-svg"></svg>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUpdated, watch } from 'vue';
import { transformer, Markmap } from '../utils/markmap';

export default {
  name: 'MindmapViewer',
  props: {
    markdown: {
      type: String,
      default: ''
    },
    isDarkMode: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const svgRef = ref();
    const wrapperRef = ref();
    let mm = null;

    const updateMindmap = async () => {
      if (!props.markdown || !mm) return;
      
      const { root } = transformer.transform(props.markdown);
      await mm.setData(root);
      mm.fit();
    };

    // 全屏切换
    const toggleFullscreen = async () => {
      const wrapper = wrapperRef.value;
      if (!wrapper) return;

      if (!document.fullscreenElement) {
        await wrapper.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
      
      // 全屏切换后重新自适应
      setTimeout(() => {
        if (mm) mm.fit();
      }, 100);
    };

    // 下载SVG文件
    const downloadSVG = () => {
      const svg = svgRef.value;
      if (!svg) return;

      // 克隆SVG以修改尺寸
      const clonedSvg = svg.cloneNode(true);
      
      // 获取SVG的实际尺寸
      const rect = svg.getBoundingClientRect();
      const width = rect.width || 800;
      const height = rect.height || 600;
      
      // 设置明确的宽高属性
      clonedSvg.setAttribute('width', width);
      clonedSvg.setAttribute('height', height);
      clonedSvg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      
      // 添加背景色
      const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      bgRect.setAttribute('width', width);
      bgRect.setAttribute('height', height);
      bgRect.setAttribute('fill', props.isDarkMode ? '#1f2937' : '#ffffff');
      clonedSvg.insertBefore(bgRect, clonedSvg.firstChild);

      // 获取SVG内容并添加XML声明
      const svgData = new XMLSerializer().serializeToString(clonedSvg);
      const svgContent = `<?xml version="1.0" encoding="UTF-8"?>\n${svgData}`;
      
      // 创建Blob并下载
      const svgBlob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);
      const link = document.createElement('a');
      link.download = `思维导图_${new Date().getTime()}.svg`;
      link.href = url;
      link.click();
      URL.revokeObjectURL(url);
    };

    onMounted(() => {
      // 创建 markmap 实例
      mm = Markmap.create(svgRef.value, {
        autoFit: true,
        fitRatio: 0.8,
        duration: 500,
        style: (id) => `
          .${id} {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          }
          .${id} .markmap-node {
            cursor: pointer;
          }
          .${id} .markmap-node-circle {
            fill: ${props.isDarkMode ? '#f43f5e' : '#f43f5e'};
            stroke: none;
          }
          .${id} .markmap-link {
            stroke: ${props.isDarkMode ? '#4b5563' : '#d1d5db'};
            stroke-width: 1.5;
          }
          .${id} .markmap-node-text {
            fill: ${props.isDarkMode ? '#e5e7eb' : '#1f2937'};
            font-size: 14px;
            font-weight: 500;
          }
          .${id} .markmap-node-foreign {
            overflow: visible;
          }
        `
      });
      
      updateMindmap();
    });

    // 监听 markdown 变化
    watch(() => props.markdown, updateMindmap);
    
    // 监听主题变化，重新渲染
    watch(() => props.isDarkMode, () => {
      if (mm) {
        updateMindmap();
      }
    });

    onUpdated(() => {
      updateMindmap();
    });

    return { svgRef, wrapperRef, toggleFullscreen, downloadSVG };
  }
};
</script>

<style scoped>
.mindmap-wrapper {
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;
}

.mindmap-wrapper:fullscreen {
  background: var(--bg-color, #ffffff);
  padding: 20px;
}

.mindmap-wrapper:fullscreen .mindmap-container {
  height: 100vh;
}

.mindmap-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.mindmap-toolbar {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 8px;
  z-index: 10;
}

.toolbar-btn {
  padding: 8px;
  border-radius: 8px;
  background: rgba(128, 128, 128, 0.1);
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: rgba(128, 128, 128, 0.2);
}

.mindmap-svg {
  width: 100%;
  height: 100%;
  min-height: 400px;
}
</style>
