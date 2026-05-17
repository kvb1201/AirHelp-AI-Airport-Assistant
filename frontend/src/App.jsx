import React, { useCallback, useState, useMemo, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import HomeContent from './components/HomeContent';
import FlightQueryModal from './components/FlightQueryModal';
import TerminalMapView from './components/TerminalMapView';
import NavigationFlowView from './components/NavigationFlowView';
import FacilitiesDirectoryView from './components/FacilitiesDirectoryView';
import LostFoundView from './components/LostFoundView';
import ChatPanel from './components/ChatPanel';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import BottomNav from './components/BottomNav';
import PlaceholderView from './components/PlaceholderView';
import CrisisContactOverlay from './components/CrisisContactOverlay';
import ReportIssueModal from './components/ReportIssueModal';
import OperationalAlertsBar from './components/OperationalAlertsBar';
import OperatorConsoleView from './components/OperatorConsoleView';
import ViewTransition from './components/ViewTransition';
import MoreMenuSheet from './components/MoreMenuSheet';
import ChatDrawer from './components/ChatDrawer';
import useMediaQuery from './hooks/useMediaQuery';
import DesignSystemShowcase from './components/DesignSystemShowcase';
import { sendChatMessage } from './services/api';

function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const WELCOME = {
  text: "You're in AirHelp for CSMIA Mumbai, Terminal 2. Ask about facilities, flights, walking routes, or issues — or say e.g. “take me to BIBA”.",
  role: 'bot',
  time: formatTime(),
};

const LOCATION_LABELS = {
  t2_entrance: 'Near Entrance',
};

const PAGE_TITLES = {
  Home: { title: 'Home', sub: 'Your T2 companion' },
  Map: { title: 'Terminal map', sub: 'Floor plan & routes' },
  Navigation: { title: 'Walking directions', sub: 'Step-by-step guidance' },
  Facilities: { title: 'Facilities', sub: 'Food, shops, lounges' },
  'Lost & Found': { title: 'Lost & Found', sub: 'Report or claim items' },
  Operator: { title: 'Operator', sub: 'Staff tools' },
  Profile: { title: 'Profile', sub: 'Account & preferences' },
};

function App() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isDesktop = useMediaQuery('(min-width: 769px)');

  const [messages, setMessages] = useState([WELCOME]);
  const [isLoading, setIsLoading] = useState(false);
  const [location, setLocation] = useState('t2_entrance');
  const [chatOpen, setChatOpen] = useState(false);
  const [mobileView, setMobileView] = useState('home');
  const [sidebarNav, setSidebarNav] = useState('Home');
  const [mapLaunch, setMapLaunch] = useState(null);
  const [guidedNavHandoff, setGuidedNavHandoff] = useState(null);
  const [crisisContact, setCrisisContact] = useState(null);
  const [showFlightModal, setShowFlightModal] = useState(false);
  const [reportIssueOpen, setReportIssueOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [showDesignSystem, setShowDesignSystem] = useState(
    () => typeof window !== 'undefined' && window.location.hash === '#design-system',
  );

  useEffect(() => {
    const onHash = () => setShowDesignSystem(window.location.hash === '#design-system');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const showMap = sidebarNav === 'Map' || mobileView === 'map';
  const showNavFlow = sidebarNav === 'Navigation' || mobileView === 'nav';
  const showFacilities = sidebarNav === 'Facilities' || mobileView === 'facilities';
  const showLostFound = sidebarNav === 'Lost & Found' || mobileView === 'lostfound';
  const showOperator = sidebarNav === 'Operator' || mobileView === 'operator';
  const showProfilePlaceholder =
    !showMap &&
    !showNavFlow &&
    !showFacilities &&
    !showLostFound &&
    (sidebarNav === 'Profile' || mobileView === 'profile');

  const showMobileChat = isMobile && mobileView === 'chat';

  const stageKey = useMemo(() => {
    if (showMobileChat) return 'chat';
    if (showMap) return 'map';
    if (showNavFlow) return 'nav';
    if (showFacilities) return 'facilities';
    if (showLostFound) return 'lostfound';
    if (showOperator) return 'operator';
    if (showProfilePlaceholder) return 'profile';
    return 'home';
  }, [
    showMobileChat,
    showMap,
    showNavFlow,
    showFacilities,
    showLostFound,
    showOperator,
    showProfilePlaceholder,
  ]);

  const pageMeta = PAGE_TITLES[sidebarNav] || PAGE_TITLES.Home;

  const openChat = useCallback(() => {
    setChatOpen(true);
    if (isMobile) setMobileView('chat');
  }, [isMobile]);

  const closeChat = useCallback(() => {
    setChatOpen(false);
    if (isMobile && mobileView === 'chat') {
      setMobileView('home');
      setSidebarNav('Home');
    }
  }, [isMobile, mobileView]);

  const clearMapLaunch = useCallback(() => setMapLaunch(null), []);
  const clearGuidedNavHandoff = useCallback(() => setGuidedNavHandoff(null), []);

  const openStepByStepFromMap = useCallback((payload) => {
    setGuidedNavHandoff({ ...payload, _id: Date.now() });
    setSidebarNav('Navigation');
    setMobileView('nav');
  }, []);

  const handleNavSelect = useCallback(
    (label) => {
      setChatOpen(false);
      setSidebarNav(label);
      if (label === 'Map') setMobileView('map');
      else if (label === 'Navigation') setMobileView('nav');
      else if (label === 'Facilities') setMobileView('facilities');
      else if (label === 'Lost & Found') setMobileView('lostfound');
      else if (label === 'Operator') setMobileView('operator');
      else if (label === 'Profile') setMobileView('profile');
      else setMobileView('home');
    },
    [],
  );

  const handleAskNav = useCallback(() => {
    openChat();
  }, [openChat]);

  const handleNewChat = useCallback(() => {
    setMessages([{ ...WELCOME, time: formatTime() }]);
    setCrisisContact(null);
    openChat();
  }, [openChat]);

  const handleMobileViewChange = useCallback(
    (view) => {
      setMoreMenuOpen(false);
      if (view === 'chat') {
        openChat();
        return;
      }
      setChatOpen(false);
      setMobileView(view);
      if (view === 'map') setSidebarNav('Map');
      else if (view === 'nav') setSidebarNav('Navigation');
      else if (view === 'home') setSidebarNav('Home');
    },
    [openChat],
  );

  const handleMoreSelect = useCallback((id) => {
    setChatOpen(false);
    setMobileView(id);
    if (id === 'facilities') setSidebarNav('Facilities');
    else if (id === 'lostfound') setSidebarNav('Lost & Found');
    else if (id === 'operator') setSidebarNav('Operator');
    else if (id === 'profile') setSidebarNav('Profile');
  }, []);

  const openFloorMap = useCallback(
    (payload) => {
      if (payload?.fromId) setLocation(payload.fromId);
      setMapLaunch(payload || null);
      handleNavSelect('Map');
    },
    [handleNavSelect],
  );

  const goToFacilityOnMap = useCallback(
    ({ graphNodeId }) => {
      openFloorMap({ fromId: location, toId: graphNodeId, routeIndex: 0 });
    },
    [location, openFloorMap],
  );

  const handleSend = async (text, loc = null, opts = {}) => {
    const currentLocation = loc ?? location;
    if (loc) setLocation(loc);
    setCrisisContact(null);

    setMessages((prev) => [...prev, { text, role: 'user', time: formatTime() }]);
    setIsLoading(true);
    openChat();

    try {
      const data = await sendChatMessage(text, currentLocation, {
        inputMode: opts.inputMode || 'text',
        whisperLang: opts.whisperLang || null,
      });
      const botText = data.message || data.response || 'Got it!';
      setMessages((prev) => [...prev, { text: botText, role: 'bot', time: formatTime() }]);

      const payload = data.data || {};
      if (payload.crisis_contact) {
        setCrisisContact({ ...payload.crisis_contact, kind: payload.special_assistance });
      }
      const navStart = payload.start;
      const navEnd = payload.end;
      const openMapForRecommendation =
        payload.open_map_after_chat &&
        (data.type === 'recommendation' || data.intent === 'recommendation');
      if (
        navStart &&
        navEnd &&
        (data.type === 'navigation' ||
          data.intent === 'navigation' ||
          openMapForRecommendation)
      ) {
        setChatOpen(false);
        openFloorMap({ fromId: navStart, toId: navEnd, routeIndex: 0 });
      }
    } catch (err) {
      console.error('API error:', err);
      setMessages((prev) => [
        ...prev,
        { text: 'Server not responding. Please try again.', role: 'error', time: formatTime() },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTicketCreated = useCallback(
    (ticket) => {
      const lines = [
        '## Ticket created',
        '',
        `Your reference is **${ticket.ticket_id}**.`,
        '',
        `- **Issue type:** ${ticket.category_label}`,
        `- **Summary:** ${ticket.summary}`,
        '',
      ];
      if (ticket.email_notice) {
        lines.push(ticket.email_sent ? ticket.email_notice : `**Note:** ${ticket.email_notice}`);
        lines.push('');
      }
      lines.push('Keep this number if you contact airport support about this report.');
      setMessages((prev) => [...prev, { text: lines.join('\n'), role: 'bot', time: formatTime() }]);
      openChat();
    },
    [openChat],
  );

  const renderStage = () => {
    if (showMobileChat) {
      return (
        <div className="mobile-chat-page">
          <div className="mobile-chat-page-header">
            <button type="button" className="mobile-chat-back" onClick={closeChat} aria-label="Back">
              <span className="ms">arrow_back</span>
            </button>
            <div>
              <h2 className="mobile-chat-page-title">AirHelp</h2>
              <p className="mobile-chat-page-sub">Ask anything about T2</p>
            </div>
          </div>
          <div className="mobile-chat-page-body">
            <ChatWindow messages={messages} isLoading={isLoading} />
          </div>
        </div>
      );
    }

    if (showMap) {
      return (
        <TerminalMapView
          location={location}
          onLocationChange={setLocation}
          launchRoute={mapLaunch}
          onLaunchRouteConsumed={clearMapLaunch}
          onOpenStepByStepGuidance={openStepByStepFromMap}
        />
      );
    }

    if (showNavFlow) {
      return (
        <NavigationFlowView
          location={location}
          onLocationChange={setLocation}
          onOpenFloorMap={openFloorMap}
          guidedHandoff={guidedNavHandoff}
          onGuidedNavHandoffConsumed={clearGuidedNavHandoff}
        />
      );
    }

    if (showFacilities) {
      return <FacilitiesDirectoryView location={location} onGoToFacility={goToFacilityOnMap} />;
    }

    if (showLostFound) {
      return <LostFoundView location={location} onOpenFloorMap={openFloorMap} />;
    }

    if (showOperator) {
      return <OperatorConsoleView onBack={() => handleNavSelect('Home')} />;
    }

    if (showProfilePlaceholder) {
      return (
        <PlaceholderView title="Profile" onBack={() => handleNavSelect('Home')} backLabel="Back to Home">
          <p>Saved trips, preferences, and account tools will show here in a future update.</p>
        </PlaceholderView>
      );
    }

    return (
      <>
        <HomeContent
          locationLabel={LOCATION_LABELS[location] || 'Near Entrance'}
          onSend={handleSend}
          onOpenNavigation={() => handleNavSelect('Navigation')}
          onOpenFloorMap={openFloorMap}
          onOpenReportIssue={() => setReportIssueOpen(true)}
          onOpenFlightQueries={() => setShowFlightModal(true)}
          onOpenChat={openChat}
        />
        <FlightQueryModal
          visible={showFlightModal}
          onClose={() => setShowFlightModal(false)}
          onSaved={(resp) => {
            const botText = resp.message || 'Flight saved.';
            setMessages((prev) => [...prev, { text: botText, role: 'bot', time: formatTime() }]);
            openChat();
          }}
        />
      </>
    );
  };

  const showMobileInput = isMobile && showMobileChat && !showOperator;
  const showMobileBottomNav = isMobile && !showOperator;

  if (showDesignSystem) {
    return (
      <DesignSystemShowcase
        onBack={() => {
          window.location.hash = '';
          setShowDesignSystem(false);
        }}
      />
    );
  }

  return (
    <div className={`app-container${stageKey === 'home' ? ' app-container--home' : ''}`}>
      {crisisContact ? (
        <CrisisContactOverlay data={crisisContact} onDismiss={() => setCrisisContact(null)} />
      ) : null}

      <ReportIssueModal
        open={reportIssueOpen}
        onClose={() => setReportIssueOpen(false)}
        graphLocationId={location}
        onTicketCreated={handleTicketCreated}
      />

      <Sidebar
        activeNav={sidebarNav}
        onNavChange={handleNavSelect}
        onNewChat={handleNewChat}
        onAsk={handleAskNav}
      />

      <div className={`app-body app-body--full${stageKey === 'home' ? ' app-body--home' : ''}`}>
        <OperationalAlertsBar />

        <header className="desktop-header" role="banner">
          <div>
            <h1 className="desktop-page-title">{pageMeta.title}</h1>
            <p className="desktop-page-sub">{pageMeta.sub}</p>
          </div>
          <div className="desktop-header-actions">
            <button type="button" className="desktop-ask-btn" onClick={openChat}>
              <span className="ms">forum</span>
              Ask AirHelp
            </button>
            <div className="header-avatar" role="button" tabIndex={0} aria-label="Guest profile">
              G
            </div>
          </div>
        </header>

        <header className="mobile-header" role="banner">
          <button type="button" className="mobile-header-menu" aria-label="Home" onClick={() => handleNavSelect('Home')}>
            <span className="ms">spa</span>
          </button>
          <div className="mobile-header-title">
            <h1>{pageMeta.title}</h1>
            <p>CSMIA · T2</p>
          </div>
          <button type="button" className="mobile-header-bell" aria-label="Ask AirHelp" onClick={openChat}>
            <span className="ms">forum</span>
          </button>
        </header>

        <div
          className={`content-area content-area--full${showMap ? ' content-area--map' : ''}${showFacilities || showLostFound || showOperator ? ' content-area--facilities' : ''}`}
        >
          <main
            className={`main-content main-content--full${showMobileChat ? ' main-content--mobile-chat' : ''}${stageKey === 'home' ? ' main-content--home' : ''}`}
          >
            <ViewTransition viewKey={stageKey} enabled={isMobile}>
              {renderStage()}
            </ViewTransition>
          </main>
        </div>

        {showMobileBottomNav ? (
          <div className={`mobile-bottom${showOperator ? ' mobile-bottom--operator' : ''}`}>
            {showMobileInput ? <InputBox onSend={handleSend} isLoading={isLoading} /> : null}
            <BottomNav activeView={mobileView} onViewChange={handleMobileViewChange} onMoreOpen={() => setMoreMenuOpen(true)} />
          </div>
        ) : null}
      </div>

      {isDesktop && !chatOpen && stageKey !== 'home' ? (
        <button
          type="button"
          className={`chat-fab${showMap ? ' chat-fab--map' : ''}`}
          onClick={openChat}
          aria-label="Open AirHelp assistant"
        >
          <span className="ms" aria-hidden="true">forum</span>
          Ask AirHelp
        </button>
      ) : null}

      {isDesktop ? (
        <ChatDrawer open={chatOpen} onClose={closeChat}>
          <ChatPanel
            messages={messages}
            isLoading={isLoading}
            onSend={handleSend}
            isOpen
            onToggle={closeChat}
            onClose={closeChat}
            mapMode={showMap && chatOpen}
            drawerMode
          />
        </ChatDrawer>
      ) : null}

      <MoreMenuSheet open={moreMenuOpen} onClose={() => setMoreMenuOpen(false)} onSelect={handleMoreSelect} />
    </div>
  );
}

export default App;
